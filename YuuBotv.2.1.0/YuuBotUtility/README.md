# YuuBot v.2.1.0 Utility - Setup & Running Instructions

![](https://img.shields.io/badge/version-2.1.0-green) ![](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python) ![](https://img.shields.io/badge/Snowflake-Data_Cloud-29B5E8?logo=snowflake) ![](https://img.shields.io/badge/Tavily-Web_Search-00A86B)

## Overview

YuuBot Utility v.2.1.0 contains the database setup scripts, ML models, semantic model configurations, and agent definitions for the YuuBot earthquake monitoring system. This utility folder provides the foundation for setting up Snowflake databases, configuring AI agents with Cortex Agents, integrating Tavily web search, and loading ML models for earthquake probability forecasting.

## Prerequisites

Before setting up YuuBot Utility v.2.1.0, ensure you have the following:

### Required Accounts
- **Snowflake Account** with ACCOUNTADMIN role (or appropriate permissions)
- **Tavily API Account** - Sign up at https://tavily.com for web search capabilities

### Required Software
- Python 3.10+
- Git

### Required Python Packages
```bash
pip install snowflake-connector-python requests python-dotenv pandas torch numpy
```

## Files Overview

```
YuuBotUtility/
├── setup.sql                      # Database, schema, stage, and ML function setup
├── YuuBotChat_AgentSetup.sql       # Agent creation with tools and instructions
├── load_csv.py                    # Script to download USGS data and upload to Snowflake
├── earthquake_prob_model_7d.pth   # PyTorch LSTM model for 7-day earthquake forecasting
└── yamls/
    ├── jp_quake_logger.yaml       # Cortex Analyst semantic model for Japan earthquakes
    └── global_quake_logger.yaml   # Cortex Analyst semantic model for global earthquakes
```

## Snowflake Setup

### Step 1: Create Database, Schema, and Stage

1. Open **Snowsight** and create a new SQL Worksheet
2. Execute the commands in `setup.sql` to create the necessary database, schema, stage, and UDF:

```sql
-- Set the database where the UDF and Stage are located
USE DATABASE YUUBOT_DB;
CREATE OR REPLACE SCHEMA MODEL;
USE SCHEMA MODEL;

CREATE OR REPLACE STAGE YUUBOT_DB.MODEL.EARTHQUAKE_STAGE
  COMMENT = 'Internal stage for earthquake data files and ML models';
```

3. Create the earthquake probability forecasting UDF:

```sql
CREATE OR REPLACE FUNCTION FORECAST_EARTHQUAKE_PROB (
    TARGET_LAT FLOAT,
    TARGET_LON FLOAT,
    RADIUS_KM NUMBER
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
PACKAGES = (
    'numpy',
    'pandas',
    'pytorch',
    'snowflake-snowpark-python'
)
IMPORTS = (
    '@EARTHQUAKE_STAGE/all_month.csv',
    '@EARTHQUAKE_STAGE/earthquake_prob_model_7d.pth'
)
HANDLER = 'forecast_handler'
AS
$$
# ... (full UDF code is in setup.sql)
$$
;
```

### Step 2: Create Warehouse (Optional)

If you don't have a warehouse, create one:

1. In Snowsight, navigate to **Admin** >> **Warehouses**
2. Click **+ Warehouse**
3. Name it `EARTHQUAKE_WH_XS` and select X-Small size
4. Click **Create Warehouse**

## Tavily API Setup

Tavily provides real-time web search capabilities for the YuuBot agent, enabling it to fetch current earthquake news and breaking seismic events.

### Step 1: Install Tavily from Snowflake Marketplace

1. In Snowsight, navigate to **Marketplace**
2. Search for "Tavily"
3. Click on **Tavily Search** and select **Get**
4. Follow the prompts to install in your account

### Step 2: Configure Tavily API

1. Get your Tavily API key from https://app.tavily.com/api-key
2. In Snowflake, navigate to **AI & ML** >> **Cortex Agents**
3. Select your agent (or create one)
4. Under **Tavily API Config**, provide your API key
5. Enable **External API access** in the API configuration settings
6. Click **Validate the Configuration**

### Step 3: Create Tavily Search Procedure

After installing Tavily from the Marketplace, execute the following in a SQL Worksheet:

```sql
-- Verify Tavily is installed
SHOW DATABASES LIKE 'TAVILY_SEARCH_API';

-- Create the web search procedure if not already created
CREATE OR REPLACE PROCEDURE TAVILY_SEARCH_API.TAVILY_SCHEMA.TAVILY_WEB_SEARCH(
    QUERY VARCHAR,
    SEARCH_DEPTH VARCHAR DEFAULT 'basic',
    MAX_RESULTS NUMBER DEFAULT 5
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
PACKAGES = ('requests')
AS
$$
import requests
import json

tavily_api_key = os.environ.get('TAVILY_API_KEY')
if not tavily_api_key:
    return {"error": "Tavily API key not configured"}

url = "https://api.tavily.com/search"
headers = {"Content-Type": "application/json"}
data = {
    "api_key": tavily_api_key,
    "query": QUERY,
    "search_depth": SEARCH_DEPTH,
    "max_results": MAX_RESULTS
}

response = requests.post(url, headers=headers, json=data)
return response.json()
$$;
```

For detailed setup instructions, follow the [Snowflake Tavily guide](https://www.snowflake.com/en/developers/guides/build-a-due-diligence-and-investment-research-agent-in-snowflake-using-tavily/).

## Loading Files to Snowflake Stage

### Step 1: Create Environment File

Create a `.env` file in the `YuuBotUtility` directory:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=EARTHQUAKE_WH_XS
SNOWFLAKE_DATABASE=YUUBOT_DB
SNOWFLAKE_SCHEMA=MODEL

# Tavily API Key (for web search)
TAVILY_API_KEY=your_tavily_api_key
```

### Step 2: Download USGS Earthquake Data

```bash
cd YuuBotUtility
python load_csv.py --output all_month.csv
```

This downloads the past month's earthquake data from USGS and saves it to `all_month.csv`.

### Step 3: Upload Files to Snowflake Stage

**Option 1: Using Snowflake SQL (Snowsight)**

Upload files to the EARTHQUAKE_STAGE:

```sql
USE DATABASE YUUBOT_DB;
USE SCHEMA MODEL;

-- Upload CSV file
PUT file://./all_month.csv @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Upload ML model
PUT file://./earthquake_prob_model_7d.pth @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Upload semantic model YAML files
PUT file://./yamls/jp_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./yamls/global_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Verify files
LIST @EARTHQUAKE_STAGE;
```

**Option 2: Using load_csv.py with Stage Upload**

```bash
python load_csv.py --output all_month.csv --upload-stage
```

This will download the CSV and upload it to Snowflake stage in one step.

## Creating the YuuBot Agent

### Step 1: Configure Cortex Analyst (Semantic Models)

Cortex Analyst enables the agent to query structured data by generating SQL using semantic views.

1. In Snowsight, navigate to **AI & ML** >> **Cortex Analyst**
2. Click **Create new** >> **Upload your YAML file**
3. Upload the semantic model files:
   - `yamls/jp_quake_logger.yaml` - For Japan earthquake data
   - `yamls/global_quake_logger.yaml` - For global earthquake data
4. Select database and schema: **YUUBOT_DB.JP** or **YUUBOT_DB.GLOBAL**
5. Click **Save**

### Step 2: Create the Agent

1. In Snowsight, navigate to **AI & ML** >> **Agents**
2. Click **Create agent**
3. Configure the agent:
   - Select **Create this agent for Snowflake Intelligence**
   - Schema: **YUUBOT_DB.GLOBAL**
   - Agent object name: `YUUBOT_CHAT`

**Option: Use SQL Script**

Alternatively, execute `YuuBotChat_AgentSetup.sql` in a SQL Worksheet:

```sql
CREATE OR REPLACE AGENT YUUBOT_DB.GLOBAL.YUUBOT_CHAT
  FROM SPECIFICATION
  $$
  -- (Full agent specification is in YuuBotChat_AgentSetup.sql)
  $$;
```

### Step 3: Add Tools to the Agent

The agent uses the following tools:

1. **GLOBAL_QUAKE_LOGGING_TOOL** (Cortex Analyst)
   - Semantic model: `global_quake_logger.yaml`
   - Database: YUUBOT_DB, Schema: GLOBAL

2. **JP_QUAKE_LOGGING_TOOL** (Cortex Analyst)
   - Semantic model: `jp_quake_logger.yaml`
   - Database: YUUBOT_DB, Schema: JP

3. **TAVILY_SEARCH_TOOL** (Generic)
   - Type: Procedure
   - Identifier: `TAVILY_SEARCH_API.TAVILY_SCHEMA.TAVILY_WEB_SEARCH`

4. **FORECAST_EARTHQUAKE_PROB_TOOL** (Generic)
   - Type: Function
   - Identifier: `YUUBOT_DB.MODEL.FORECAST_EARTHQUAKE_PROB`

### Step 4: Add Instructions

Add the following orchestration instructions:

> "If the user specifies global earthquakes in the prompt, the agent must use the GLOBAL_QUAKE_LOGGING_TOOL tool. If the user specifies Japan earthquakes in their prompt, the agent must use the JP_QUAKE_LOGGING_TOOL tool. If the user asks about current events or news related to earthquakes, use the TAVILY_SEARCH_TOOL. Dismiss questions that are not related to earthquakes."

### Step 5: Add Example Questions

- "How many earthquakes were recorded in Japan?"
- "What's the most recent global earthquake?"
- "Forecast the earthquake probability for Tokyo in the next 7 days."

### Step 6: Save and Test

1. Click **Save** to save the agent configuration
2. Test the agent by asking questions through YuuLite or YuuBotMain

## Features

- **Earthquake Probability Forecasting**: LSTM-based ML model for predicting 7-day earthquake probability
- **Real-time Web Search**: Tavily integration for current earthquake news and breaking events
- **Natural Language Queries**: Cortex Analyst enables SQL generation from natural language
- **Multi-region Support**: Queries both Japan and global earthquake data
- **Semantic Models**: YAML-based configurations for structured data access
- **Snowflake Integration**: Full integration with Snowflake Cortex Agents and Intelligence

## Troubleshooting

### Common Issues

1. **"Error connecting to Snowflake"**
   - Verify your Snowflake credentials in `.env`
   - Check that your account identifier is correct
   - Ensure your warehouse is running

2. **Tavily API errors**
   - Ensure Tavily is installed from Snowflake Marketplace
   - Verify your Tavily API key is valid
   - Enable external API access in Snowflake settings

3. **Agent not finding semantic models**
   - Verify YAML files are uploaded to the stage
   - Check that Cortex Analyst is configured with the correct database/schema
   - Ensure tool resources point to the correct stage path

4. **ML model loading errors**
   - Ensure `earthquake_prob_model_7d.pth` is uploaded to the Snowflake stage
   - Verify the stage path in the UDF imports matches the actual stage

5. **"Access denied to trial accounts"**
   - As of Snowflake's policy, trial accounts may have restricted Cortex AI access
   - Consider converting to a paid account for full functionality
   - Alternatively, create a Cortex Code CLI trial account

## Architecture

```
YuuBot Utility v.2.1.0
├── Database Setup (setup.sql)
│   ├── YUUBOT_DB database
│   ├── MODEL schema
│   ├── EARTHQUAKE_STAGE
│   └── FORECAST_EARTHQUAKE_PROB UDF (PyTorch LSTM)
├── Agent Setup (YuuBotChat_AgentSetup.sql)
│   ├── YUUBOT_CHAT agent
│   └── Tools: Cortex Analyst, Tavily Search, ML Forecasting
├── Data Loading (load_csv.py)
│   ├── USGS GeoJSON download
│   └── Snowflake stage upload
├── Semantic Models (yamls/)
│   ├── jp_quake_logger.yaml
│   └── global_quake_logger.yaml
└── ML Model
    └── earthquake_prob_model_7d.pth (LSTM neural network)
```

## Technology Stack

- **Database**: Snowflake (YUUBOT_DB with JP, GLOBAL, and MODEL schemas)
- **AI/ML**: Snowflake Cortex Agents, Cortex Analyst, PyTorch
- **Web Search**: Tavily API
- **Data Processing**: Python, Pandas, NumPy
- **Languages**: SQL, Python, YAML

## References

- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Tavily Search Integration Guide](https://www.snowflake.com/en/developers/guides/build-a-due-diligence-and-investment-research-agent-in-snowflake-using-tavily/)
- [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)
- [Tavily API Documentation](https://docs.tavily.com/)

## License

This project is part of the YuuBot earthquake monitoring system.
