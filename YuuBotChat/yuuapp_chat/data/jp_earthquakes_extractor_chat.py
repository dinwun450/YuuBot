import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime

def JSTtoPST(the_time):
    dt = datetime.strptime(the_time, '%Y年%m月%d日 %H時%M分ごろ')
    timezone = pytz.timezone('Asia/Tokyo')
    jst = timezone.localize(dt)
    return jst.strftime('%Y-%m-%d %H:%M:%S')

def get_earthquake_data():
    r = requests.get("https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/")
    soup = BeautifulSoup(r.content, 'html.parser')
    earthquakes_history = soup.find('table', class_="yjw_table")
    content_of_earthquakes = earthquakes_history.find_all('tr')
    content_of_earthquakes.pop(0)
    quake_info = []
    appendation_of_date = []
    c = 0

    for i in content_of_earthquakes:
        quake_info.append(i.find_all("td"))

    while c < len(quake_info):
        date, time = JSTtoPST(quake_info[c][0].text).split(" ")[0], JSTtoPST(quake_info[c][0].text).split(" ")[1]
        d = {}
        
        d["date"] = date
        d["time"] = time
        d["epicenter"] = quake_info[c][1].text

        if d["mag"] == "---":
            d["mag"] = None
        else:
            d["mag"] = float(quake_info[c][2].text)
            
        d["intensity"] = quake_info[c][3].text
        
        if d["intensity"] == "---":
            d["intensity"] = "---"

        appendation_of_date.append(d)
        c += 1

    return appendation_of_date
