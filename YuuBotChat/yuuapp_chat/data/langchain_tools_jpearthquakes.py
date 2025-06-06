from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

def get_earthquake_data() -> list:
    """
    Fetches the latest earthquake data from the Yahoo Japan weather website.
    Returns a list of dictionaries containing earthquake details such as date, epicenter, magnitude, and intensity.
    """
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
        datetime_split = quake_info[c][0].text.split(" ")
        d = {}

        d["date"] = datetime_split[0]
        d["time"] = datetime_split[1]
        d["epicenter"] = quake_info[c][1].text
        d["mag"] = quake_info[c][2].text
        d["intensity"] = quake_info[c][3].text

        appendation_of_date.append(d)
        c += 1

    return appendation_of_date

@tool
def count_earthquakes() -> int:
    """
    Counts the number of earthquakes recorded on the Yahoo Japan weather website.
    Returns the total count of earthquakes as an integer.
    """
    all_data = get_earthquake_data()
    return len(all_data)

@tool
def get_earthquake_data_by_date(date) -> list:
    """
    Fetches earthquake data for a specific date.
    :param tool_input: The date in the format 'YYYY年M月DD日'.
    Returns a list of dictionaries containing earthquake details for that date.
    """

    all_data = get_earthquake_data()
    filtered_data = [quake for quake in all_data if quake['date'] == date]
    if not filtered_data:
        return [{"error": "No earthquakes found for the specified date."}]
    return filtered_data

@tool
def get_earthquake_data_by_time(time) -> list:
    """
    Fetches earthquake data for a specific time.
    :param tool_input: The date in the format 'HH時MM分ごろ'.
    Returns a list of dictionaries containing earthquake details for that time.
    """

    all_data = get_earthquake_data()
    filtered_data = [quake for quake in all_data if quake['time'] == time]
    if not filtered_data:
        return [{"error": "No earthquakes found for the specified time."}]
    return filtered_data


@tool
def get_earthquake_data_by_magnitude(tool_input) -> list:
    """
    Fetches earthquake data for earthquakes with a magnitude greater than or equal to the specified value.
    :param tool_input: The minimum magnitude to filter earthquakes.
    Returns a list of dictionaries containing earthquake details that meet the criteria.
    """
    try:
        min_magnitude = float(tool_input)
    except (ValueError, TypeError):
        return []
    all_data = get_earthquake_data()
    filtered_data = [quake for quake in all_data if float(quake['mag']) >= min_magnitude]
    return filtered_data

@tool
def get_earthquake_data_by_intensity(tool_input) -> list:
    """
    Fetches earthquake data for earthquakes with a specific intensity or shindo scale.
    :param tool_input: The intensity level or shindo scale to filter earthquakes (e.g., '1', '2', etc.).
    Returns a list of dictionaries containing earthquake details that meet the criteria.
    """
    intensity = tool_input if isinstance(tool_input, str) else str(tool_input)
    all_data = get_earthquake_data()
    filtered_data = [quake for quake in all_data if quake['intensity'] == intensity]
    if not filtered_data:
        return [{"error": "No earthquakes found for the specified intensity."}]
    return filtered_data

@tool
def filter_earthquakes_by_two_or_more_factors(date=None, time=None, magnitude=None, intensity=None) -> list:
    """
    Filters earthquake data based on two or more factors: date, magnitude, and intensity.
    :param date: The date in the format 'YYYY年M月DD日' (optional).
    :param time: The time in the format 'HH時MM分ごろ' (optional).
    :param magnitude: The minimum magnitude to filter earthquakes (optional).
    :param intensity: The intensity level to filter earthquakes (optional).
    Returns a list of dictionaries containing earthquake details that meet the criteria.
    """
    all_data = get_earthquake_data()
    
    if date:
        all_data = [quake for quake in all_data if quake['date'] == date]

    if time:
        all_data = [quake for quake in all_data if quake['time'] == time]
    
    if magnitude is not None:
        try:
            min_magnitude = float(magnitude)
            all_data = [quake for quake in all_data if float(quake['mag']) >= min_magnitude]
        except (ValueError, TypeError):
            return []
    
    if intensity:
        all_data = [quake for quake in all_data if quake['intensity'] == intensity]
    
    return all_data
