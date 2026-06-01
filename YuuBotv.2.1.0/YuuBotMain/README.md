# YuuBot v.2.1.0 Main - Setup & Running Instructions

![](https://img.shields.io/badge/version-2.1.0-green) ![](https://img.shields.io/badge/Next.js-16.2.6-000000?logo=next.js) ![](https://img.shields.io/badge/React-19-61DAFB?logo=react) ![](https://img.shields.io/badge/Snowflake-Data_Cloud-29B5E8?logo=snowflake)

## Overview

YuuBot Main v.2.1.0 is a real-time earthquake data visualization web application built with Next.js that displays earthquake information from Japan and globally. This version features an interactive dashboard with tabbed interface, interactive map visualization using Leaflet, and Snowflake for data storage.

## Prerequisites

Before running YuuBot Main v.2.1.0, ensure you have the following:

### Required Accounts
- **Snowflake Account** - A 30-Day Snowflake Trial. For more information, go to https://signup.snowflake.com/

### Required Software
- Node.js 18+
- npm, yarn, pnpm, or bun
- Git

### Required npm Packages
```bash
npm install
```
All dependencies are listed in `package.json` and include:
- Next.js 16.2.6
- React 19
- snowflake-sdk
- CopilotKit
- Leaflet & React-Leaflet

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

### Create Environment File

Create a `.env.local` file in the `YuuBotMain` directory:

```bash
# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=EARTHQUAKE_WH_XS
SNOWFLAKE_DATABASE=YUUBOT_DB
SNOWFLAKE_SCHEMA=JP
```

**To find your account identifier:**
1. In Snowsight, click on your account name in the bottom-left
2. Hover over your account and click the copy icon next to the account identifier

## Running YuuBot Main v.2.1.0

### Step 1: Navigate to the Project Directory

```bash
cd YuuBotv.2.1.0/YuuBotMain
```

### Step 2: Install Dependencies

```bash
npm install
# or
yarn install
# or
pnpm install
# or
bun install
```

### Step 3: Run the Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

### Step 4: Access the Web Interface

Open your browser and navigate to:
```
http://localhost:3000
```

## Features

- **Real-time Earthquake Monitoring**: Automatically fetches and displays the latest earthquake data from Japan and globally
- **Tabbed Interface**: Overview, Japan, Global, Map, and About sections
- **Japan Earthquakes**: Data including date, time, epicenter, magnitude, and Shindo intensity scale
- **Global Earthquakes**: Data including date, time, location, magnitude, and tsunami warnings
- **Interactive Map Visualization**: Leaflet-based map with color-coded markers (teal for Japan, purple for global)
  - Circle size based on magnitude
  - Popup details on click
  - Auto-fit bounds to data points
- **Advanced Filtering**: Filter earthquakes by date, magnitude, intensity (Japan), and tsunami warnings (Global)
- **Search Functionality**: Search earthquakes by date, location, magnitude, or tsunami
- **Data Refresh**: Manual refresh buttons for updating earthquake data
- **Snowflake Integration**: Uses Snowflake Cortex Agents for AI-powered data analysis

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/snowflake/overall?schema=JP` | Get all Japan earthquake data |
| `/api/snowflake/overall?schema=GLOBAL` | Get all global earthquake data |
| `/api/snowflake/overall?schema=JP&limit=N` | Get N most recent Japan earthquakes |
| `/api/snowflake/overall?schema=GLOBAL&limit=N` | Get N most recent global earthquakes |

## Troubleshooting

### Common Issues

1. **"Error connecting to Snowflake" message**
   - Verify your Snowflake credentials in `.env.local`
   - Check that your account identifier is correct
   - Ensure your warehouse is running

2. **Empty earthquake data**
   - Verify the YUUBOT_DB database and JP/GLOBAL schemas exist
   - Populate the tables with earthquake data using data refresh scripts

3. **Map not loading**
   - Ensure Leaflet CSS is properly loaded
   - Check browser console for JavaScript errors
   - Verify network access to OpenStreetMap tiles

4. **Module not found errors**
   - Ensure all dependencies are installed: `npm install`

5. **Port already in use**
   - Kill the process using the port or change the port in next.config.ts

## Architecture

```
YuuBot Main v.2.1.0
├── Next.js Frontend (src/app/)
│   ├── page.tsx (Dashboard with tabs)
│   ├── layout.tsx (Root layout)
│   └── providers.tsx (CopilotKit providers)
├── Components (src/components/)
│   ├── quake-map.tsx (Leaflet map component)
│   ├── headless-chat.tsx (CopilotKit chat UI)
│   └── tool-rendering.tsx (Agent tool display)
├── API Routes (src/app/api/)
│   └── snowflake/route.ts (Snowflake data endpoints)
├── Library (src/lib/)
│   ├── snowflake.ts (Snowflake connection)
│   ├── earthquake-refresh.ts (Data refresh logic)
│   └── utils.ts (Utility functions)
├── Snowflake Connector
│   └── Connection management via snowflake-sdk
└── Data Sources
    ├── USGS Earthquake API (Global)
    └── Yahoo Japan Weather (Japan)
```

## Technology Stack

- **Framework**: Next.js 16.2.6 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Database**: Snowflake (YUUBOT_DB with JP and GLOBAL schemas)
- **Mapping**: Leaflet, React-Leaflet, OpenStreetMap tiles
- **AI Integration**: CopilotKit, Snowflake Cortex Agents
- **Analytics**: Weights & Biases Weave

## Data Sources

- **Global Earthquakes**: [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) - Weekly earthquake feed
- **Japan Earthquakes**: [Yahoo Japan Weather](https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/) - Recent Japan earthquake data

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowflake Python Connector](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
- [Leaflet Documentation](https://leafletjs.com/)
- [React-Leaflet Documentation](https://react-leaflet.js.org/)
- [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/)
- [CopilotKit Documentation](https://docs.copilotkit.ai/)

## License

This project is part of the YuuBot earthquake monitoring system.
