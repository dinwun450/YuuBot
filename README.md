# YuuBot

![](https://img.shields.io/badge/version-1.2.1-green) ![GitHub last commit](https://img.shields.io/github/last-commit/dinwun450/YuuBot) ![GitHub Repo stars](https://img.shields.io/github/stars/dinwun450/YuuBot)

## Overview
YuuBot is a comprehensive earthquake monitoring system for Japan and globally. It consists of two integrated components: a real-time earthquake data visualization web application and an AI-powered chatbot interface. The system continuously tracks, stores, presents, and forecasts earthquake data from Japan and other parts of the world, making critical seismic information accessible through visual dashboards and natural language interactions.

## Key Features

### YuuBotWeb - Data Visualization Platform
- **Real-time Earthquake Monitoring**: Automatically extracts and displays the latest earthquake data from Yahoo Japan Weather and USGS' API (v1.2.1 Web)
- **Interactive Dashboard**: Presents earthquake information including date, epicenter location, magnitude, Shindo (Japanese seismic intensity scale), and tsunami (for Global Earthquakes, v1.2.1 Web)
- **Data Persistence**: Utilizes ScyllaDB (Cassandra-compatible database) for reliable storage across a three-node cluster (For legacy versions). As of v.1.2.1, it utilizes Snowflake for storage among the two schemas, including Global ones.
- **Responsive Design**: Web and Chat interface optimized for both desktop and mobile viewing

### YuuBotChat - AI-Powered Earthquake Information Assistant
- **Natural Language Interface**: Interact with earthquake data through conversational queries
- **Advanced Data Analysis**: Powered by Google's Gemini AI model through LangChain integration (Legacy). For YuuBot v.1.2.1, it's powered by Snowflake Intelligence through Cortex Agents. Other AI models may be implemented soon for further use in advanced data analysis.
- **Specialized Query Tools**: Filter earthquakes by date, magnitude, intensity, or multiple criteria simultaneously
- **Statistical Analysis**: Generate counts and summaries of earthquake activity while forecasting the probability of significant earthquakes (as of v.1.2.1)

## Technology Stack
- **Backend**: Flask (Web), Streamlit (Chat)
- **Database**: ScyllaDB (Cassandra-compatible), Snowflake (For Web and Chat v.1.2.1)
- **AI/ML**: LangChain, LangGraph, Google Gemini AI, Snowflake Intelligence / Cortex Agents (For Web and Chat v.1.2.1)
- **Data Processing**: BeautifulSoup, Requests
- **Containerization**: Docker, Docker Compose
- **Analytics and Tracing**: Weights & Biases' Weave (For Chat v.1.2.1)

## Use Cases
- **Disaster Monitoring**: Track seismic activity in real-time for emergency response
- **Research**: Analyze earthquake patterns and frequencies in Japan and globally
- **Public Information**: Provide accessible earthquake data for general awareness
- **Educational Tool**: Learn about Japan or global's seismic activity through interactive exploration
- **Real-time Quake Monitoring**: Use the real-time NIED or other global earthquake sensors map to track each earthquake's events (Coming soon).

## Getting Started
The application is containerized for easy deployment. To start the systems in the Chat and Web sections, use Docker Compose. For more information, check out the ReadME files in the Chat and Web directories. As of YuuBot Web and Chat v.1.2.1 for starting the systems, users can simply run the Python Flask app or Streamlit app.

## Note
YuuBot Chat (Legacy) requires a Google API key for the Gemini AI model integration. Gemini LLMs may hallucinate at any time. As of v.1.2.1 for YuuBot Web and Chat, a Snowflake account is required while a W&B account is strongly recommended. YuuBot is under development, meaning that some missing features will be released soon. YuuBot Chat v.1.2.1 instructions will be posted soon.

## My Socials
[![Static Badge](https://img.shields.io/badge/Instagram-magenta?logo=instagram&logoColor=white)](https://www.instagram.com/dinwun450/) [![LinkedIn](https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff)](https://www.linkedin.com/in/dinowun) [![Facebook](https://img.shields.io/badge/Facebook-%231877F2.svg?logo=Facebook&logoColor=white)](https://www.facebook.com/dino.wun.5)

