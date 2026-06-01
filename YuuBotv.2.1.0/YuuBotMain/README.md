# YuuBot Main v.2.1.0 - Setup & Running Instructions

![](https://img.shields.io/badge/version-2.1.0-green) ![](https://img.shields.io/badge/Snowflake-Intelligence-29B5E8?logo=snowflake) ![](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=fff) ![](https://img.shields.io/badge/React-%2320232a.svg?logo=react&logoColor=%2361DAFB)

## Overview

YuuBot Main v.2.1.0 is a real-time earthquake data visualization web application that displays earthquake information from Japan and globally, and also has a chatbot for leveraging **Snowflake Intelligence** to provide natural language interactions. This version uses **Snowflake** for data storage and provides an interactive dashboard with earthquake monitoring capabilities, uses Snowflake's Cortex Agents for advanced data analysis and earthquake probability forecasting, and is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app), courtesy of **Copilotkit**.

## Prerequisites
Before running YuuBot Main v.2.1.0, ensure you have the following:

### Required Accounts
* Snowflake Account - A 30-day Snowflake Trial with Cortex Code CLI. For more information, go to https://signup.snowflake.com/ and then to "Cortex Code CLI for Developers".

### Required Setup
See instructions in the YuuBotUtility directory.

## Getting Started

First, install the packages:

```bash
npm install
# or
yarn install
# or
pnpm install
#or
bun install
```

Next, open the ".env" file and replace the placeholders for your Snowflake account, username, and password.

Lastly, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.
