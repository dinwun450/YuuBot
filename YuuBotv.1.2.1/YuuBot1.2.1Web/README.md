# YuuBot v.1.2.1 Web - Setup & Running Instructions

![](https://img.shields.io/badge/version-1.2.1-green) ![](https://img.shields.io/badge/Flask-3.x-000000?logo=flask) ![](https://img.shields.io/badge/Snowflake-Data_Cloud-29B5E8?logo=snowflake)

## Overview

YuuBot Web v.1.2.1 is a real-time earthquake data visualization web application that displays earthquake information from Japan and globally. This version uses **Snowflake** for data storage and provides an interactive dashboard with earthquake monitoring capabilities.

## Prerequisites

Before running YuuBot Web v.1.2.1, ensure you have the following:

### Required Accounts
- **Snowflake Account** - A 30-Day Snowflake Trial. For more information, go to https://signup.snowflake.com/

### Required Software
- Python 3.10+
- Git

### Required Python Packages
```bash
pip install flask snowflake-connector-python requests scrapy beautifulsoup4
```

## Snowflake Setup

### Step 1: Create Database and Schemas

1. In the Snowflake Platform, go to `Catalog > Database Explorer`, then click on the "+ Database" button on the top-right corner.
2. Type "YUUBOT_DB" as the database name, then click "Create".
3. While you're in the "YUUBOT_DB", Click on "+ Schema" button on the top-right corner, then type "JP" as the schema name, then click "Create".
4. Repeat for creating the "GLOBAL" schema.

### Step 2: Create Warehouse (Optional)

If you don't have a warehouse, create one:

1. In Snowsight, navigate to **Admin** >> **Warehouses**
2. Click **+ Warehouse**
3. Name it `EARTHQUAKE_WH_XS` and select X-Small size
4. Click **Create Warehouse**

## Environment Configuration

### Update Snowflake Credentials

Edit `snowflake_data/the_main_connector.py` and update the following credentials:

```python
conn = snowflake.connector.connect(
    user="your_username",
    password="your_password",
    account="your_account_identifier",
    warehouse="EARTHQUAKE_WH_XS",
    database="YUUBOT_DB",
    schema=schema
)
```

**To find your account identifier:**
1. In Snowsight, click on your account name in the bottom-left
2. Hover over your account and click the copy icon next to the account identifier

## Running YuuBot Web v.1.2.1

### Step 1: Navigate to the Project Directory

```bash
cd YuuBot1.2.1Web
```

### Step 2: Run the Flask Application

```bash
python yuubot_1.2.1_app.py
```

### Step 3: Access the Web Interface

View your running app from Flask via **Port 4092** shown in the terminal.

Open your browser and navigate to:
```
http://localhost:4092
```

## Features

- **Real-time Earthquake Monitoring**: Automatically fetches and displays the latest earthquake data
- **Japan Earthquakes**: Data from Yahoo Japan Weather including date, time, epicenter, magnitude, and intensity (Shindo scale)
- **Global Earthquakes**: Data from USGS API including date, time, location, magnitude, and tsunami warnings
- **Interactive Dashboard**: View earthquake data in tabular format
- **Map Visualization**: Geographic coordinates for earthquake mapping
- **Data Refresh**: Manual refresh endpoints for updating earthquake data

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard with Japan and global earthquake data |
| `/refresh_global` | Refresh global earthquake data |
| `/refresh_jp` | Refresh Japan earthquake data |
| `/jp_coordinates` | Get Japan earthquake coordinates (JSON) |
| `/global_coordinates` | Get global earthquake coordinates (JSON) |
| `/count_global_earthquakes` | Get total count of global earthquakes |
| `/count_jp_earthquakes` | Get total count of Japan earthquakes |
| `/count_significant_global_earthquakes` | Count earthquakes with magnitude ≥ 5.0 (global) |
| `/count_significant_jp_earthquakes` | Count earthquakes with magnitude ≥ 5.0 (Japan) |

## Troubleshooting

### Common Issues

1. **"Error connecting to Snowflake" message**
   - Verify your Snowflake credentials in `snowflake_data/the_main_connector.py`
   - Check that your account identifier is correct
   - Ensure your warehouse is running

2. **Empty earthquake data**
   - Verify the YUUBOT_DB database and JP/GLOBAL schemas exist
   - Check your network connection for fetching external data

3. **Port already in use**
   - Change the port in `yuubot_1.2.1_app.py`:
     ```python
     app.run(debug=True, host='0.0.0.0', port=YOUR_PORT)
     ```

4. **Module not found errors**
   - Ensure all required packages are installed:
     ```bash
     pip install flask snowflake-connector-python requests scrapy beautifulsoup4
     ```

## Architecture

```
YuuBot Web v.1.2.1
├── Flask Backend (yuubot_1.2.1_app.py)
│   ├── Route Handlers
│   └── Data Refresh Functions
├── Snowflake Connectors (snowflake_data/)
│   ├── the_main_connector.py (Connection management)
│   └── quakes_overall_conn.py (Data insertion)
├── Frontend (templates/)
│   └── index.html (Dashboard UI)
├── Static Assets (static/)
│   ├── style.css
│   ├── background-images/
│   └── shindo-images/
└── Data Sources
    ├── USGS Earthquake API (Global)
    └── Yahoo Japan Weather (Japan)
```

## Data Sources

- **Global Earthquakes**: [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) - Weekly earthquake feed
- **Japan Earthquakes**: [Yahoo Japan Weather](https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/) - Recent Japan earthquake data

## References

- [Snowflake Documentation](https://docs.snowflake.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)

## License

This project is part of the YuuBot earthquake monitoring system.
