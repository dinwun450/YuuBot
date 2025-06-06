# YuuBot

## Overview
YuuBot is a comprehensive earthquake monitoring system for Japan, consisting of two integrated components: a real-time earthquake data visualization web application and an AI-powered chatbot interface. The system continuously tracks, stores, and presents earthquake data from Japan, making critical seismic information accessible through both visual dashboards and natural language interactions.

## Key Features

### YuuBotWeb - Data Visualization Platform
- **Real-time Earthquake Monitoring**: Automatically extracts and displays the latest earthquake data from Yahoo Japan Weather
- **Interactive Dashboard**: Presents earthquake information including date, epicenter location, magnitude, and shindo (Japanese seismic intensity scale)
- **Data Persistence**: Utilizes ScyllaDB (Cassandra-compatible database) for reliable storage across a three-node cluster
- **Responsive Design**: Web interface optimized for both desktop and mobile viewing

### YuuBotChat - AI-Powered Earthquake Information Assistant
- **Natural Language Interface**: Interact with earthquake data through conversational queries
- **Advanced Data Analysis**: Powered by Google's Gemini AI model through LangChain integration
- **Specialized Query Tools**: Filter earthquakes by date, magnitude, intensity, or multiple criteria simultaneously
- **Statistical Analysis**: Generate counts and summaries of earthquake activity

## Technology Stack
- **Backend**: Flask (Web), Streamlit (Chat)
- **Database**: ScyllaDB (Cassandra-compatible)
- **AI/ML**: LangChain, LangGraph, Google Gemini AI
- **Data Processing**: BeautifulSoup, Requests
- **Containerization**: Docker, Docker Compose

## Use Cases
- **Disaster Monitoring**: Track seismic activity in real-time for emergency response
- **Research**: Analyze earthquake patterns and frequencies in Japan
- **Public Information**: Provide accessible earthquake data for general awareness
- **Educational Tool**: Learn about Japan's seismic activity through interactive exploration

## Getting Started
The application is containerized for easy deployment. Use Docker Compose to start the entire system:

```bash
cd YuuBotWeb
docker-compose up -d
```

Access the web interface at http://localhost:4092 and the chat interface at http://localhost:8501

## Note
YuuBot Chat requires a Google API key for the Gemini AI model integration.
