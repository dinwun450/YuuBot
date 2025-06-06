import requests
from bs4 import BeautifulSoup

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
        d = {}
        d["date"] = quake_info[c][0].text
        d["epicenter"] = quake_info[c][1].text
        d["mag"] = quake_info[c][2].text
        d["intensity"] = quake_info[c][3].text
        
        if d["intensity"] == "---":
            d["intensity"] = "---"
        else:
            d["intensity"] = f"shindo-images/tbp{quake_info[c][3].text}.png"

        appendation_of_date.append(d)
        c += 1

    return appendation_of_date