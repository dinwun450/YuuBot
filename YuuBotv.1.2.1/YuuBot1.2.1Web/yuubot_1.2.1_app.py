from flask import Flask, render_template, jsonify
from snowflake_data.the_main_connector import create_snowflake_connection
from snowflake_data.quakes_overall_conn import insert_overall_data_to_snowflake
import snowflake.connector

def refresh_jp_quakes():
    insert_overall_data_to_snowflake("JP")

def refresh_global_quakes():
    insert_overall_data_to_snowflake("GLOBAL")

def get_global_quakes():
    refresh_global_quakes()
    conn = create_snowflake_connection("GLOBAL")
    try:
        cur = conn.cursor()
        cur.execute("SELECT date, time, magnitude, location, title, tsunami FROM all_earthquakes_week ORDER BY date DESC, time DESC")
        rows = cur.fetchall()
        return rows
    except snowflake.connector.Error as e:
        print(f"Error fetching global earthquakes: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_jp_quakes():
    refresh_jp_quakes()
    conn = create_snowflake_connection("JP")
    try:
        cur = conn.cursor()
        cur.execute("SELECT date, time, epicenter, magnitude, intensity FROM all_jp_earthquakes WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY date DESC, time DESC")
        rows = cur.fetchall()
        return rows
    except snowflake.connector.Error as e:
        print(f"Error fetching Japan earthquakes: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_most_recent_earthquake_jp():
    conn = create_snowflake_connection("JP")
    try:
        cur = conn.cursor()
        cur.execute("SELECT date, time, epicenter, magnitude, intensity FROM all_jp_earthquakes WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY date DESC LIMIT 1")
        rows = cur.fetchall()
        print(rows)
        return rows
    except snowflake.connector.Error as e:
        print(f"Error fetching Japan earthquakes: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_most_recent_earthquake_global():
    conn = create_snowflake_connection("GLOBAL")
    try:
        cur = conn.cursor()
        cur.execute("SELECT date, time, magnitude, location, tsunami FROM all_earthquakes_week ORDER BY date DESC, time DESC LIMIT 1")
        rows = cur.fetchall()
        return rows
    except snowflake.connector.Error as e:
        print(f"Error fetching global earthquakes: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

app = Flask(__name__)
@app.route('/')

def index():
    jp_quakes = get_jp_quakes()
    global_quakes = get_global_quakes()
    recent_quakes = {
        "jp": get_most_recent_earthquake_jp(),
        "global": get_most_recent_earthquake_global()
    }

    return render_template('index.html', jp_quakes=jp_quakes, global_quakes=global_quakes, recent_quakes_jp=recent_quakes["jp"], recent_quakes_global=recent_quakes["global"])

@app.route('/refresh_global')
def refresh_global():
    refresh_global_quakes()
    recent = get_most_recent_earthquake_global()
    return jsonify({
        "global_quakes": get_global_quakes(),
        "recent_global": recent
    })

@app.route('/refresh_jp')
def refresh_jp():
    refresh_jp_quakes()
    recent = get_most_recent_earthquake_jp()
    return jsonify({
        "jp_quakes": get_jp_quakes(),
        "recent_jp": recent
    })

@app.route('/jp_coordinates')
def get_jp_coordinates():
    conn = create_snowflake_connection("JP")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT lat, lon, date, time, intensity, epicenter, magnitude "
            "FROM all_jp_earthquakes WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY date DESC, time DESC"
        )
        rows = cur.fetchall()
        coordinates = []
        for row in rows:
            coordinates.append({
                "lat": row[0],
                "lon": row[1],
                "date": str(row[2]) if row[2] is not None else None,
                "time": str(row[3]) if row[3] is not None else None,
                "intensity": row[4],
                "epicenter": row[5],
                "magnitude": float(row[6]) if row[6] is not None else None
            })
        return jsonify(coordinates)
    except snowflake.connector.Error as e:
        print(f"Error fetching JP coordinates: {e}")
        return jsonify([])
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/global_coordinates')
def get_global_coordinates():
    conn = create_snowflake_connection("GLOBAL")
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT lat, lon, date, time, magnitude, location, title, tsunami FROM all_earthquakes_week ORDER BY date DESC, time DESC"
        )
        rows = cur.fetchall()
        coordinates = []
        for row in rows:
            coordinates.append({
                "lat": row[0],
                "lon": row[1],
                "date": str(row[2]) if row[2] is not None else None,
                "time": str(row[3]) if row[3] is not None else None,
                "magnitude": float(row[4]) if row[4] is not None else None,
                "location": row[5],
                "title": row[6],
                "tsunami": bool(row[7]) if row[7] is not None else None
            })
        return jsonify(coordinates)
    except snowflake.connector.Error as e:
        print(f"Error fetching Global coordinates: {e}")
        return jsonify([])
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/count_global_earthquakes')
def count_global_quakes():
    conn = create_snowflake_connection("GLOBAL")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM all_earthquakes_week")
        count = cur.fetchone()[0]
        return jsonify({"count": count})
    except snowflake.connector.Error as e:
        print(f"Error counting global earthquakes: {e}")
        return jsonify({"count": 0})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/count_jp_earthquakes')
def count_jp_quakes():
    conn = create_snowflake_connection("JP")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM all_jp_earthquakes WHERE lat IS NOT NULL AND lon IS NOT NULL")
        count = cur.fetchone()[0]
        return jsonify({"count": count})
    except snowflake.connector.Error as e:
        print(f"Error counting Japan earthquakes: {e}")
        return jsonify({"count": 0})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route("/count_significant_global_earthquakes")
def count_significant_global_quakes():
    conn = create_snowflake_connection("GLOBAL")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM all_earthquakes_week WHERE magnitude >= 5.0")
        count = cur.fetchone()[0]
        return jsonify({"count": count})
    except snowflake.connector.Error as e:
        print(f"Error counting significant global earthquakes: {e}")
        return jsonify({"count": 0})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route("/count_significant_jp_earthquakes")
def count_significant_jp_quakes():
    conn = create_snowflake_connection("JP")
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM all_jp_earthquakes WHERE magnitude >= 5.0 AND lat IS NOT NULL AND lon IS NOT NULL")
        count = cur.fetchone()[0]
        return jsonify({"count": count})
    except snowflake.connector.Error as e:
        print(f"Error counting significant Japan earthquakes: {e}")
        return jsonify({"count": 0})
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0' , port=4092)  # Adjust host and port as needed
