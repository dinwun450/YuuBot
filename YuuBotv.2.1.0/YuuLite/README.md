# YuuBot v.2.1.0 Lite - Setup & Running Instructions

![](https://img.shields.io/badge/version-2.1.0-green) ![](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit) ![](https://img.shields.io/badge/Snowflake-Cortex_Agents-29B5E8?logo=snowflake) ![](https://img.shields.io/badge/Weave-Cost_Tracking-FFBE0B?logo=weightsandbiases)

## Overview

YuuBot Lite v.2.1.0 is an AI-powered earthquake information assistant that leverages **Snowflake Cortex Agents** to provide natural language interactions with earthquake data from Japan and globally. This version uses Claude AI models through Snowflake's AI infrastructure for advanced data analysis, earthquake forecasting, and real-time web search capabilities.

## Prerequisites

Before running YuuBot Lite v.2.1.0, ensure you have the following:

### Required Accounts
- **Snowflake Account** with ACCOUNTADMIN role (or appropriate permissions) in a region with access to [supported models](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence#supported-models-and-regions)
- **Weights & Biases (W&B) Account** (strongly recommended for analytics and cost tracking)

### Required Software
- Python 3.10+
- Git

### Required Python Packages
```bash
pip install streamlit numpy pandas requests sseclient weave snowflake-connector-python python-dotenv
```

## Snowflake Setup

### Step 1: Create Database and Agent

Ensure you have followed the setup instructions in **YuuBotUtility/README.md** to:
1. Create the `YUUBOT_DB` database with `JP`, `GLOBAL`, and `MODEL` schemas
2. Set up the `EARTHQUAKE_STAGE` and upload required files
3. Create the `YUUBOT_CHAT` agent with all tools configured

### Step 2: Generate a Personal Access Token (PAT)

1. In Snowsight, click on your profile >> **My Profile**
2. Navigate to **Authentication** >> **Personal Access Tokens**
3. Click **Generate Token** and copy the token
4. Set the expiration period (recommended: 90 days)

### Step 3: Create Environment File

Create a `.env` file in the `YuuLite` directory:

```bash
# Snowflake Configuration
SNOWFLAKE_PAT=your_personal_access_token
SNOWFLAKE_HOST=your_account_identifier.snowflakecomputing.com

# Weights & Biases (optional but recommended)
WANDB_API_KEY=your_wandb_api_key
```

**To find your Snowflake host:**
1. In Snowsight, click on your account name in the bottom-left
2. Hover over your account and click the copy icon
3. Your host is: `{account_identifier}.snowflakecomputing.com`

## Running YuuBot Lite v.2.1.0

### Step 1: Navigate to the Project Directory

```bash
cd YuuBotv.2.1.0/YuuLite
```

### Step 2: Unzip Models (if models.zip exists)

```bash
unzip models.zip
```

This extracts the required model files for the chat application.

### Step 3: Run the Streamlit Application

```bash
streamlit run yuubot_chat.py
```

The application will start and display a URL (typically `http://localhost:8501`).

### Step 4: Access the Chat Interface

Open your browser and navigate to the URL shown in the terminal. You'll see the YuuBot Lite interface.

### Streamlit Configuration (Optional)

Create a `.streamlit/config.toml` file for custom configuration:

```toml
[server]
port = 8501
headless = true

[theme]
primaryColor = "#446A43"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## Features

### Natural Language Interface
- Ask questions in plain English about earthquakes
- Get instant responses with formatted data

### Snowflake Cortex Agents Integration
- Powered by Claude AI models (Claude 4 Sonnet, Claude 3.5 Sonnet)
- Access to structured earthquake data through Cortex Analyst

### Real-time Streaming Responses
- Streaming agent responses with thinking visualization
- Live tool use and result display
- Request ID tracking for debugging

### Rich Data Visualization
- Dynamically renders charts from agent responses
- Interactive tables with earthquake data
- Expandable sections for detailed information

### Cost Tracking with Weave
- Weights & Biases Weave integration for monitoring
- Token consumption tracking
- Cost analysis per conversation

### Event Trace Analysis
- On-demand event trace analysis in sidebar
- Event counts and sample data
- Token usage statistics
- Debug agent behavior

### Tavily Web Search Integration
- Real-time web search for current earthquake news
- Breaking seismic event information
- Research capabilities beyond database data

## Usage Examples

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

### Current Events
- "What are the latest earthquake news today?"
- "Are there any breaking seismic events?"

## Architecture

```
YuuBot Lite v.2.1.0
├── Streamlit Frontend (yuubot_chat.py)
│   ├── Chat Interface
│   ├── Message Rendering (text, charts, tables)
│   └── Sidebar Event Analysis
├── Snowflake Integration
│   ├── REST API Client (agent_run)
│   ├── Event Streaming (SSE)
│   └── Weave Cost Tracking
├── Data Models (models/)
│   ├── Message, ContentItem
│   ├── ChartEventData, TableEventData
│   └── ToolUseEventData, ToolResultEventData
└── Analytics
    └── Weights & Biases (Weave)
```

## Troubleshooting

### Common Issues

1. **"Missing env vars" warning**
   - Ensure your `.env` file is in the `YuuLite` directory
   - Verify all required environment variables are set

2. **Authentication errors**
   - Verify your PAT is valid and not expired
   - Check that your Snowflake host is correct

3. **Agent not found**
   - Ensure the agent name in the code (`YUUBOT_CHAT`) matches the one created in Snowflake
   - Verify the database and schema paths: `YUUBOT_DB.GLOBAL.YUUBOT_CHAT`

4. **Empty responses or no data**
   - Verify earthquake data exists in `YUUBOT_DB.JP` and `YUUBOT_DB.GLOBAL` schemas
   - Check that semantic models are properly configured in Cortex Analyst

5. **Streamlit port already in use**
   - Kill the existing process or change the port in `.streamlit/config.toml`

6. **Weave initialization errors**
   - Ensure `WANDB_API_KEY` is set if using Weave
   - Check network connectivity to Weights & Biases

## Technology Stack

- **Frontend**: Streamlit (Python)
- **AI/ML**: Snowflake Cortex Agents, Claude AI models
- **Analytics**: Weights & Biases Weave
- **Database**: Snowflake (YUUBOT_DB)
- **Web Search**: Tavily API
- **Data Processing**: Pandas, NumPy

## References

- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence)
- [Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Weave Documentation](https://docs.wandb.ai/weave)
- [Tavily Search Integration](https://www.snowflake.com/en/developers/guides/build-a-due-diligence-and-investment-research-agent-in-snowflake-using-tavily/)
- [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)

## License

This project is part of the YuuBot earthquake monitoring system.