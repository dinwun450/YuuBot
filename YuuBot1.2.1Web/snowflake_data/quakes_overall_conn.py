import snowflake.connector
import requests
import re
from datetime import datetime
from snowflake_data.the_main_connector import create_snowflake_connection
from concurrent.futures import ThreadPoolExecutor
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from bs4 import BeautifulSoup

url = "https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/"
html = requests.get(url).text
response = HtmlResponse(url=url, body=html, encoding='utf-8')
selector = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@class="yjw_main_md"]/div[@id="eqhist"]/table/tr/td').getall()[4:]

def convert_timestamp_to_date(timestamp):
    try:
        # Validate the timestamp
        if timestamp > 1e10:  # If the timestamp is in milliseconds, convert to seconds
            timestamp = timestamp / 1000
        date_time = datetime.fromtimestamp(timestamp)
        formatted_date = date_time.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date
    except (OSError, ValueError) as e:
        print(f"Invalid timestamp: {timestamp}. Error: {e}")
        return "Invalid date"
    
def convert_jp_timestamp_to_date(jp_timestamp):
    try:
        date_time = datetime.strptime(jp_timestamp, '%Y年%m月%d日 %H時%M分ごろ')
        formatted_date = date_time.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date
    except (OSError, ValueError) as e:
        print(f"Invalid JP timestamp: {jp_timestamp}. Error: {e}")
        return "Invalid date"
    
def check_tsunami(value):
    if value == 0:
        return False
    else:
        return True

def get_usgs_earthquakes_from_past_week():
    all_quakes = []
    try:
        url = f'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson'

        headers = {
            "Content-Type": "application/geo+json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors first
        quakeData = response.json()
        
        current_earthquakes = quakeData.get('features')
        if not current_earthquakes:
            print("Earthquake data not available.")
            
        for quake in current_earthquakes:
            magnitude = quake.get('properties', {}).get('mag', 'N/A')

            # Filter out earthquakes with magnitude less than 2.0
            if magnitude is None or magnitude < 2.0:
                continue
            
            location = quake.get('properties', {}).get('place', 'N/A')
            date = convert_timestamp_to_date(int(quake.get('properties', {}).get('time', 'N/A'))).split(" ")[0]
            time = convert_timestamp_to_date(int(quake.get('properties', {}).get('time', 'N/A'))).split(" ")[1]
            title = quake.get('properties', {}).get('title', 'N/A')
            tsunami = check_tsunami(quake.get('properties', {}).get('tsunami', 'N/A'))
            coordinates = quake.get('geometry', {}).get('coordinates', [None, None])
            lon = coordinates[0] if len(coordinates) > 0 else None
            lat = coordinates[1] if len(coordinates) > 1 else None
            all_quakes.append((date, time, magnitude, location, title, tsunami, lat, lon))

        return all_quakes

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    
def extract_jp_quake_info(url):
    html = requests.get(url).text
    response = HtmlResponse(url=url, body=html, encoding='utf-8')
    coords_extracted = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@id="yjw_keihou"]/div[@id="eqinfdtl"]/table[@class="yjw_table boderset"]/tr/td').getall()[11]
    mag_extracted = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@id="yjw_keihou"]/div[@id="eqinfdtl"]/table[@class="yjw_table boderset"]/tr/td').getall()[7]
    shindo_extracted = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@id="yjw_keihou"]/div[@id="eqinfdtl"]/table[@class="yjw_table boderset"]/tr/td').getall()[5]
    location_extracted = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@id="yjw_keihou"]/div[@id="eqinfdtl"]/table[@class="yjw_table boderset"]/tr/td').getall()[3]
    datetime_extracted = Selector(response).xpath('/html/body/div[@id="wrapper"]/div[@id="contents"]/div[@id="contents-body"]/div[@id="main"]/div[@id="yjw_keihou"]/div[@id="eqinfdtl"]/table[@class="yjw_table boderset"]/tr/td').getall()[1]

    coords_match = re.search(r"北緯([0-9.]+)度/東経([0-9.]+)度", Selector(text=coords_extracted).xpath('string()').get().strip())
    mag_match = re.search(r"([0-9.]+)", Selector(text=mag_extracted).xpath('string()').get().strip())
    shindo_match = re.search(r"([0-9.]+)", Selector(text=shindo_extracted).xpath('string()').get().strip())
    location_match = re.search(r"(.+)", Selector(text=location_extracted).xpath('string()').get().strip())

    # extract raw datetime text
    raw_datetime = Selector(text=datetime_extracted).xpath('string()').get().strip()
    # try to find an epoch timestamp (10-13 digits: seconds or milliseconds)
    num_match = re.search(r'(\d{10,13})', raw_datetime)
    if num_match:
        ts = int(num_match.group(1))
        converted = convert_timestamp_to_date(ts)
    else:
        # fallback: try the JP formatted timestamp conversion
        converted = convert_jp_timestamp_to_date(raw_datetime)

    # create a small match-like object so later code using datetime_match.group(1) still works
    class _DummyMatch:
        def __init__(self, s):
            self._s = s
        def group(self, n):
            return self._s

    datetime_match = _DummyMatch(converted) if converted and converted != "Invalid date" else None
    date = datetime_match.group(1).split(" ")[0] if datetime_match else None
    time = datetime_match.group(1).split(" ")[1] if datetime_match else None

    if coords_match:
        intensity_text = Selector(text=shindo_extracted).xpath('string()').get().strip()
        intensity_match2 = re.search(r'([0-9]+(?:\.[0-9]+)?)(?:\s*([強弱]))?', intensity_text)
        intensity = (intensity_match2.group(1) + (intensity_match2.group(2) or '')) if intensity_match2 else '---'

        return {
            "date": date,
            "time": time,
            "magnitude": mag_match.group(1) if mag_match else None,
            "intensity": intensity,
            "location": location_match.group(1) if location_match else None,
            "latitude": coords_match.group(1),
            "longitude": coords_match.group(2),
        }
    return {"date": None, "time": None, "magnitude": None, "intensity": "---", "location": None, "latitude": None, "longitude": None}

def process_jp_quake(i):
    cell = re.sub(r'<td(?:\s+align="center")?>', '', selector[i]).replace('</td>', '').strip()
    soup = BeautifulSoup(cell, 'html.parser')
    a_tag = soup.find('a')
    link = a_tag['href'] if a_tag and a_tag.has_attr('href') else None
    if link:
        return extract_jp_quake_info("https://typhoon.yahoo.co.jp/" + link)
    return {"date": None, "time": None, "magnitude": None, "intensity": "---", "location": None, "latitude": None, "longitude": None}

def get_jp_quake_info_list():
    num_quakes = len(selector) // 4
    quake_info_list = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_jp_quake, i*4) for i in range(num_quakes)]
        for future in futures:
            quake_info_list.append(future.result())
    
    return quake_info_list

def global_or_jp(schema, ins_cur):
    if schema == "GLOBAL":
        ins_cur.execute("""
            CREATE OR REPLACE TABLE all_earthquakes_week (
                date STRING,
                time STRING,
                magnitude FLOAT,
                location STRING,
                title STRING,
                tsunami BOOLEAN,
                lat FLOAT,
                lon FLOAT
            )
        """)

        data_to_insert = get_usgs_earthquakes_from_past_week()
        insert_sql = "INSERT INTO all_earthquakes_week (date, time, magnitude, location, title, tsunami, lat, lon) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        ins_cur.executemany(insert_sql, data_to_insert)
    elif schema == "JP":
        ins_cur.execute("""
            CREATE OR REPLACE TABLE all_jp_earthquakes (
                date STRING,
                time STRING,
                epicenter STRING,
                magnitude STRING,
                intensity STRING,
                lat FLOAT,
                lon FLOAT
            )
        """)
    
        data_dicts = get_jp_quake_info_list()
        data_to_insert = []
        for d in data_dicts:
            data_to_insert.append((
                d.get("date"),
                d.get("time"),
                d.get("location"),
                float(d.get("magnitude")) if d.get("magnitude") not in (None, '') else None,
                d.get("intensity"),
                float(d.get("latitude")) if d.get("latitude") not in (None, '') else None,
                float(d.get("longitude")) if d.get("longitude") not in (None, '') else None,
            ))
        insert_sql = "INSERT INTO all_jp_earthquakes (date, time, epicenter, magnitude, intensity, lat, lon) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        ins_cur.executemany(insert_sql, data_to_insert)
    else:
        print("Invalid schema specified. Use 'GLOBAL' or 'JP'.")

def insert_overall_data_to_snowflake(schema):
    the_conn = create_snowflake_connection(schema)

    try:
        # 2. Create a cursor object
        cur = the_conn.cursor()

        # 3. Insert data based on schema
        global_or_jp(schema, cur)

        # 4. Commit the transaction
        the_conn.commit()

        print(f"{cur.rowcount} records inserted successfully.")
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        # Rollback the transaction if an error occurs
        the_conn.rollback()
    finally:
        # 5. Close the cursor and connection
        if cur:
            cur.close()
        if the_conn:
            the_conn.close()