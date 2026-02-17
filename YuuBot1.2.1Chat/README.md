# YuuBot v.1.2.1 Chat - Setup & Running Instructions

![](https://img.shields.io/badge/version-1.2.1-green) ![](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit) ![](https://img.shields.io/badge/Snowflake-Intelligence-29B5E8?logo=snowflake)

## Overview

YuuBot Chat v.1.2.1 is an AI-powered earthquake information assistant that leverages **Snowflake Intelligence** to provide natural language interactions with earthquake data from Japan and globally. This version uses Snowflake's Cortex Agents for advanced data analysis and earthquake probability forecasting.

## Prerequisites

Before running YuuBot Chat v.1.2.1, ensure you have the following:

### Required Accounts
- **Snowflake Account** with ACCOUNTADMIN role (or appropriate permissions) in a region with access to [supported models](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence#supported-models-and-regions)
- **Weights & Biases (W&B) Account** (strongly recommended for analytics and tracing)

### Required Software
- Python 3.10+
- Git

### Required Python Packages
```bash
pip install streamlit numpy pandas requests sseclient-py weave snowflake-connector-python python-dotenv scrapy beautifulsoup4
```

## Snowflake Intelligence Setup

This section guides you through setting up Snowflake Intelligence components required for YuuBot Chat v.1.2.1. For more details, refer to the [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/) guide.

### Step 1: Database and Schema Setup

1. Open **Snowsight** and create a new SQL Worksheet
2. Execute the commands in `setup.sql` to create the necessary database, schema, stage, and UDF:

```sql
-- Set the database where the UDF and Stage are located
USE DATABASE YUUBOT_DB;
CREATE OR REPLACE SCHEMA MODEL;
USE SCHEMA MODEL;

-- Create internal stage for earthquake data files and ML models
CREATE OR REPLACE STAGE YUUBOT_DB.MODEL.EARTHQUAKE_STAGE
  COMMENT = 'Internal stage for earthquake data files and ML models';
```

3. Upload required files to the stage:
```sql
PUT file://./all_month.csv @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./earthquake_prob_model_7d.pth @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./yamls/jp_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://./yamls/global_quake_logger.yaml @YUUBOT_DB.MODEL.EARTHQUAKE_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

### Step 2: Configure Cortex Analyst (Semantic Models)

Cortex Analyst enables the agent to query structured data by generating SQL using semantic views.

1. In Snowsight, navigate to **AI & ML** >> **Cortex Analyst**
2. Click **Create new** >> **Upload your YAML file**
3. Upload both semantic model files:
   - `yamls/jp_quake_logger.yaml` - For Japan earthquake data
   - `yamls/global_quake_logger.yaml` - For global earthquake data
4. Select database and schema: **YUUBOT_DB.JP** or **YUUBOT_DB.GLOBAL** >> **SEMANTIC_MODELS**
5. Click **Save**

### Step 3: Configure Cortex Search (Optional - for unstructured data)

If you want to enable search over unstructured text data (e.g., earthquake reports), set up Cortex Search:

1. In Snowsight, navigate to **AI & ML** >> **Cortex Search**
2. Click **Create** and configure:
   - Select appropriate database and schema
   - Configure search columns and attributes
   - Set up the warehouse for indexing

### Step 4: Create the Agent

1. In Snowsight, navigate to **AI & ML** >> **Agents**
2. Click **Create agent**
3. Configure the agent:
   - Select **Create this agent for Snowflake Intelligence**
   - Schema: **SNOWFLAKE_INTELLIGENCE.AGENTS**
   - Agent object name: `YUUBOT_CHAT_V121`
   - Display name: `YuuBot Chat v.1.2.1`

#### Add Instructions
Add the following under **Example questions**:
- "How many earthquakes were recorded in Japan?"
- "What's the most recent global earthquake?"
- "Forecast the earthquake probability for Tokyo in the next 7 days"

#### Add Tools

**Cortex Analyst Tools:**
1. **JP_QUAKE_LOGGING_TOOL**
   - Semantic model: `jp_quake_logger.yaml`
   - Database: YUUBOT_DB, Schema: JP
   - Description: Japan earthquake logging and analysis

2. **GLOBAL_QUAKE_LOGGING_TOOL**
   - Semantic model: `global_quake_logger.yaml`
   - Database: YUUBOT_DB, Schema: GLOBAL
   - Description: Global earthquake monitoring

**Custom Tools:**
3. **MODEL_QUAKE_FORECASTER**
   - Type: User-Defined Function (UDF)
   - Function: `FORECAST_EARTHQUAKE_PROB(TARGET_LAT, TARGET_LON, RADIUS_KM)`
   - Description: Earthquake probability forecasting using LSTM neural network

#### Orchestration Instructions
Add the following planning instruction:
> "If the user specifies global earthquakes in the prompt, the agent must use the 'GLOBAL_QUAKE_LOGGING_TOOL' tool. If the user specifies Japan earthquakes in their prompt, the agent must use the 'JP_QUAKE_LOGGING_TOOL' tool. Dismiss questions that are not related to earthquakes."

4. Click **Save** to save the agent configuration

## Environment Configuration

### Step 1: Create Environment File

Create a `.env` file in the `YuuBot1.2.1Chat` directory:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=EARTHQUAKE_WH_XS
SNOWFLAKE_DATABASE=YUUBOT_DB
SNOWFLAKE_SCHEMA=GLOBAL

# Weights & Biases (optional but recommended)
WANDB_API_KEY=your_wandb_api_key
```

### Step 2: Update Application Configuration

Edit `yuubot_1.2.1_chat.py` and update the following variables at the top of the file:

```python
PAT = "your_snowflake_personal_access_token"  # Snowflake PAT
HOST = "your_snowflake_account.snowflakecomputing.com"  # Snowflake host
DATABASE = "YUUBOT_DB"
SCHEMA = "GLOBAL"
AGENT = "YUUBOT_CHAT_V121"
```

**To generate a Personal Access Token (PAT):**
1. In Snowsight, click on your profile >> **My Profile**
2. Navigate to **Authentication** >> **Personal Access Tokens**
3. Click **Generate Token** and copy the token

## Data Refresh

Before running the application, populate the earthquake data tables.

### Option 1: Using refresh_data.py

Update the Snowflake credentials in `refresh_data.py`:

```python
conn = snowflake.connector.connect(
    user="your_username",
    password="your_password",
    account="your_account",
    warehouse="EARTHQUAKE_WH_XS",
    database="YUUBOT_DB",
    schema=schema
)
```

Then run:
```bash
python refresh_data.py
```

This will populate both the `GLOBAL` and `JP` schemas with earthquake data.

### Option 2: Using load_csv.py (for ML model data)

```bash
# Download USGS earthquake data and optionally upload to Snowflake stage
python load_csv.py --output all_month.csv --upload-stage
```

## Running YuuBot Chat v.1.2.1 with Streamlit

### Step 1: Unzip Models (if not done)

If `models.zip` exists, unzip it to extract the required model files:
```bash
unzip models.zip
```

### Step 2: Run the Streamlit Application

```bash
cd YuuBot1.2.1Chat
streamlit run yuubot_1.2.1_chat.py
```

The application will start and display a URL (typically `http://localhost:8501`).

### Step 3: Access the Chat Interface

Open your browser and navigate to the URL shown in the terminal. You'll see the YuuBot Chat v.1.2.1 interface.

### Streamlit Configuration (Optional)

Create a `.streamlit/config.toml` file for custom configuration:

```toml
[server]
port = 8501
headless = true

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## Usage Examples

Once the application is running, you can ask questions like:

### Japan Earthquakes
- "How many earthquakes were recorded in Japan?"
- "What is the most recent earthquake in Japan?"
- "Show me significant earthquakes in Japan (magnitude > 5.0)"
- "What was the earthquake intensity in 三陸沖?"

### Global Earthquakes
- "How many earthquakes occurred globally this week?"
- "What's the most recent earthquake that triggered a tsunami?"
- "Show me the trend of earthquake magnitudes"

### Earthquake Forecasting
- "Forecast earthquake probability for latitude 35.6762, longitude 139.6503 (Tokyo) within 500km radius"
- "What's the 7-day earthquake probability for California?"

## Features

- **Natural Language Interface**: Ask questions in plain English
- **Real-time Data**: Access up-to-date earthquake information
- **Visualizations**: Charts and tables generated automatically
- **Event Tracing**: Sidebar analysis of agent events (via W&B Weave integration)
- **ML Forecasting**: 7-day earthquake probability predictions using LSTM neural network

## Troubleshooting

### Common Issues

1. **"Missing env vars" warning**
   - Ensure your `.env` file is in the correct directory
   - Verify all required environment variables are set

2. **Authentication errors**
   - Verify your PAT is valid and not expired
   - Check that your Snowflake account identifier is correct

3. **Agent not found**
   - Ensure the agent name in the code matches the one created in Snowflake
   - Verify the database and schema paths

4. **Model loading errors**
   - Ensure `earthquake_prob_model_7d.pth` is uploaded to the Snowflake stage
   - Check that the stage path is correct in the UDF

5. **Cross-region inference**
   - If your region doesn't support the required models, enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference/)
6. **Network Policy is Required**
   - Go to Goverance and Security -> Network Policy -> "+ Network Policy" -> Add Name (and description since it's optional) -> "+ Create Rule" -> Create. Activate it afterwards.

## Architecture

```
YuuBot Chat v.1.2.1
├── Streamlit Frontend (yuubot_1.2.1_chat.py)
│   └── User Interface & Event Rendering
├── Snowflake Intelligence
│   ├── Cortex Agent (YUUBOT_CHAT_V121)
│   ├── Cortex Analyst (Semantic Models)
│   │   ├── JP_QUAKE_LOGGER (Japan data)
│   │   └── GLOBAL_QUAKE_LOGGER (Global data)
│   └── Custom UDF (FORECAST_EARTHQUAKE_PROB)
├── Data Sources
│   ├── USGS Earthquake API (Global)
│   └── Yahoo Japan Weather (Japan)
└── Analytics
    └── Weights & Biases (Weave)
```

## References

- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence)
- [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)

## License

This project is part of the YuuBot earthquake monitoring system.
