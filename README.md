<p align="center">
  <img src="https://github.com/dinwun450/YuuBot/blob/main/YuuBot.png" alt="Description">
</p>

---

![](https://img.shields.io/badge/version-2.1.0-green) ![GitHub last commit](https://img.shields.io/github/last-commit/dinwun450/YuuBot) ![GitHub Repo stars](https://img.shields.io/github/stars/dinwun450/YuuBot)

## Overview
YuuBot v.2.1.0 is a comprehensive earthquake monitoring system for Japan and globally. It consists of three integrated components: a real-time earthquake data visualization web application (Next.js), an AI-powered chatbot interface (Streamlit), and a lightweight AI assistant for quick queries. The system continuously tracks, stores, presents, and forecasts earthquake data from Japan and other parts of the world, making critical seismic information accessible through visual dashboards, interactive maps, and natural language interactions.

## Key Features

### YuuBotMain (Web Dashboard - Next.js)
- **Real-time Earthquake Monitoring**: Automatically displays the latest earthquake data from Japan and global sources (v.2.1.0)
- **Interactive Dashboard**: Presents earthquake information including date, time, epicenter location, magnitude, Shindo (Japanese seismic intensity scale), and tsunami warnings
- **Interactive Map Visualization**: Leaflet-based map displaying earthquake epicenters with color-coded markers for Japan (teal) and global (purple) earthquakes, with circle size based on magnitude
- **Advanced Filtering**: Filter earthquakes by date, magnitude, intensity (Japan), and tsunami warnings (Global)
- **Tabbed Interface**: Overview, Japan, Global, Map, and About sections
- **Data Persistence**: Utilizes Snowflake for reliable storage across JP and GLOBAL schemas

### YuuLite (AI-Powered Chat - Streamlit)
- **Natural Language Interface**: Interact with earthquake data through conversational queries
- **Powered by Snowflake Cortex Agents**: Uses Claude AI models (Claude 4 Sonnet, Claude 3.5 Sonnet) through Snowflake's AI infrastructure
- **Streaming Responses**: Real-time streaming of agent responses with thinking, tool use, and result visualization
- **Rich Data Visualization**: Dynamically renders charts and tables from agent responses
- **Cost Tracking**: Weave integration for monitoring LLM token consumption and costs
- **Event Trace Analysis**: On-demand event trace analysis for debugging and optimization

### YuuBotUtility
- **Earthquake Probability Forecasting**: PyTorch-based ML model for predicting earthquake probability within 7 days
- **Database Setup**: SQL scripts for configuring Snowflake database schemas and AI agents

## Technology Stack
- **Frontend**: Next.js 16.2.6 (React 19, TypeScript, Tailwind CSS v4), Streamlit (Chat)
- **Database**: Snowflake (YUUBOT_DB with JP and GLOBAL schemas)
- **AI/ML**: Snowflake Cortex Agents, Claude AI models, CopilotKit, Weights & Biases Weave, PyTorch
- **Mapping**: Leaflet, React-Leaflet, OpenStreetMap tiles
- **Data Processing**: Pandas, NumPy, BeautifulSoup, Requests
- **Containerization**: Docker, Docker Compose

## Directory Structure
```
YuuBot/
├── YuuBotv.2.1.0/
│   ├── YuuBotMain/         # Next.js web dashboard
│   ├── YuuLite/             # Streamlit AI chatbot
│   └── YuuBotUtility/       # Database setup and ML models
├── YuuBotv.1.2.1/          # Legacy versions
└── YuuBotLegacy/           # Legacy versions
```

## Getting Started

### YuuBotMain (Web Dashboard)
```bash
cd YuuBotv.2.1.0/YuuBotMain
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) with your browser.

### YuuLite (AI Chat)
```bash
cd YuuBotv.2.1.0/YuuLite
pip install -r requirements.txt
streamlit run yuubot_chat.py
```
Requires Snowflake connection credentials (SNOWFLAKE_PAT, SNOWFLAKE_HOST) and optionally Weights & Biases API key (WANDB_API_KEY).

## Use Cases
- **Disaster Monitoring**: Track seismic activity in real-time for emergency response
- **Research**: Analyze earthquake patterns and frequencies in Japan and globally
- **Public Information**: Provide accessible earthquake data for general awareness
- **Educational Tool**: Learn about Japan's and global seismic activity through interactive exploration
- **AI-Assisted Analysis**: Use natural language to query earthquake data and generate forecasts

## Note
YuuBot v.2.1.0 requires a Snowflake account for data storage and AI agent functionality. A Weights & Biases account is recommended for cost tracking in YuuLite. YuuBot is under active development, with additional features planned for future releases.

## My Socials
[![Static Badge](https://img.shields.io/badge/Instagram-magenta?logo=instagram&logoColor=white)](https://www.instagram.com/dinwun450/) [![LinkedIn](https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff)](https://www.linkedin.com/in/dinowun) [![Facebook](https://img.shields.io/badge/Facebook-%231877F2.svg?logo=Facebook&logoColor=white)](https://www.facebook.com/dino.wun.5)