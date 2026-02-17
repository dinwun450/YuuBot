# Instructions for Running YuuBot Web v.1.2.1

## Prerequisites
* A 30-Day Snowflake Trial. For more information, go to https://signup.snowflake.com/

## Steps
1. In the Snowflake Platform, go to `Catalog > Database Explorer`, then click on the "+ Database" button on the top-right corner.
2. Type "YUUBOT_DB" as the database name, then click "Create".
3. While you're in the "YUUBOT_DB", Click on "+ Schema" button on the top-right corner, then type "JP" as the schema name, then click "Create".
4. Repeat for creating the "GLOBAL" schema.
5. On the `YuuBot1.2.1Web` folder, run
   ```
   python yuubot_1.2.1_app.py
   ```
   View your running app from Flask via Port 4092 shown in the terminal.
