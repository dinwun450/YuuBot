from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel
from data.jp_earthquakes_extractor import get_earthquake_data
from data.date_of_earthquakes import extract_date
from flask import Flask, render_template

class YuuBotApp:
    def __init__(self):
        self.cluster = Cluster(contact_points=["scylla-node-mirai", "scylla-node-yuuki", "scylla-node-mari"])
        self.session = self.cluster.connect(keyspace="earthquakes")
        self.session.default_consistency_level = ConsistencyLevel.QUORUM

    def create_earthquake_table(self):
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS earthquake_data (
                date TEXT,
                epicenter TEXT,
                magnitude TEXT,
                shindo TEXT,
                PRIMARY KEY (date, epicenter)
            )
        """)

    def show_earthquake_data(self):
        result = self.session.execute(query="SELECT * FROM earthquake_data")
        for row in result:
            print(row.date, row.epicenter, row.magnitude, row.shindo)

    def flask_show_earthquake_data(self):
        result = self.session.execute(query="SELECT * FROM earthquake_data")
        return result
        
    def add_earthquake(self, date, epicenter, magnitude, shindo):
        self.session.execute(
            "INSERT INTO earthquake_data (date, epicenter, magnitude, shindo) VALUES (%s, %s, %s, %s)",
            (date, epicenter, magnitude, shindo)
        )
        
    def delete_all_earthquakes(self):
        self.session.execute("DROP TABLE earthquake_data")

    def refresh_earthquake_data(self):
        self.delete_all_earthquakes()
        self.create_earthquake_table()
        earthquake_data = get_earthquake_data()

        for data in earthquake_data:
            self.add_earthquake(data["date"], data["epicenter"], data["mag"], data["intensity"])

    def stop(self):
        self.cluster.shutdown()
    
app = Flask(__name__)
@app.route('/')

def index():
    yuuapp = YuuBotApp()
    earthquake_data = get_earthquake_data()

    for data in earthquake_data:
        yuuapp.add_earthquake(data["date"], data["epicenter"], data["mag"], data["intensity"])

    quake_display = sorted(yuuapp.flask_show_earthquake_data(), key=extract_date, reverse=True)
    return render_template('index.html', quakes=quake_display)

@app.route('/refresh')
def refresh():
    yuuapp = YuuBotApp()
    yuuapp.refresh_earthquake_data()
    print("Earthquake data refreshed.")
    quake_display = yuuapp.flask_show_earthquake_data()
    # Convert result to a list of lists
    quakes_list = sorted([[row.date, row.epicenter, row.magnitude, row.shindo] for row in quake_display], key=extract_date, reverse=True)
    return quakes_list

if __name__ == "__main__":
    app.static_folder = 'static'
    app.run(debug=True, host='0.0.0.0', port=4092)  # Adjust host and port as needed