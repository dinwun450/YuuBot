CREATE OR REPLACE AGENT YUUBOT_DB.GLOBAL.YUUBOT_CHAT
  PROFILE = '{"display_name": "YuuBot Chat v.1.2.2", "avatar": "GlobeAgentIcon", "color": "var(--x11sbcwy)"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  instructions:
    response: "The agent must provide its response in bullet points. If the location is written in Japanese, translate it to English. Use any visualizations if the user says is necessary in their prompt."
    orchestration: "If the user specifies global earthquakes in the prompt, the agent must use the GLOBAL_QUAKE_LOGGING_TOOL tool. If the user specifies Japan earthquakes in their prompt, the agent must use the JP_QUAKE_LOGGING_TOOL tool. If the user asks about current events or news related to earthquakes, use the TAVILY_SEARCH_TOOL. Dismiss questions that are not related to earthquakes."
    sample_questions:
      - question: "How many earthquakes are recorded in Japan?"
      - question: "What's the most recent global earthquake?"
      - question: "Forecast the earthquake probability for Tokyo in the next 7 days."

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "GLOBAL_QUAKE_LOGGING_TOOL"
        description: |
          ALL_EARTHQUAKES_WEEK:
          - Database: YUUBOT_DB, Schema: GLOBAL
          - Contains detailed records of global earthquake events within a one-week period, including location, magnitude, and tsunami warnings.
          - Provides comprehensive tracking of seismic activities with temporal and spatial information.
          - LIST OF COLUMNS: DATE (earthquake occurrence date), TIME (time of earthquake), LOCATION (geographical location of earthquake), TITLE (descriptive text of earthquake event), TSUNAMI (boolean indicating tsunami generation), MAGNITUDE (earthquake magnitude measurement)

          REASONING:
          This semantic model focuses on global earthquake monitoring and tracking, with emphasis on recent seismic activities within a week's timeframe.

          DESCRIPTION:
          The GLOBAL_QUAKE_LOGGER semantic model provides a comprehensive system for tracking and analyzing global earthquake events over a weekly period.
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "JP_QUAKE_LOGGING_TOOL"
        description: |
          ALL_JP_EARTHQUAKES:
          - Database: YUUBOT_DB, Schema: JP
          - Contains comprehensive records of earthquakes that occurred in Japan, capturing essential seismic event details.
          - Enables tracking and analysis of earthquake patterns, intensities, and locations across Japan.
          - LIST OF COLUMNS: DATE (earthquake occurrence date), TIME (time of earthquake), EPICENTER (location in Japanese), INTENSITY (shindo scale measurement), MAGNITUDE (earthquake magnitude measurement)

          REASONING:
          This semantic model focuses on tracking and analyzing earthquake events in Japan through a single comprehensive table.

          DESCRIPTION:
          The JP_QUAKE_LOGGER semantic model provides a comprehensive system for logging and analyzing earthquake events throughout Japan.
    - tool_spec:
        type: "generic"
        name: "TAVILY_SEARCH_TOOL"
        description: |
          Searches the web using Tavily for current earthquake news, recent seismic events, and real-time information not available in the database.
          Use this tool when the user asks about breaking news, current events, or information that may not yet be in the earthquake logs.
        input_schema:
          type: "object"
          properties:
            query:
              type: "string"
              description: "The search query to look up on the web"
            search_depth:
              type: "string"
              description: "Search depth - 'basic' or 'advanced'"
            max_results:
              type: "number"
              description: "Maximum number of results to return"
          required:
            - query
            - search_depth
            - max_results
    - tool_spec:
        type: "generic"
        name: "FORECAST_EARTHQUAKE_PROB_TOOL"
        description: |
          Advanced machine learning function that predicts the probability of significant seismic events (magnitude >= 4.5) over the next 7 days for a specified geographic location and radius.
        input_schema:
          type: "object"
          properties:
            TARGET_LAT:
              type: "number"
              description: "Target latitude"
            TARGET_LON:
              type: "number"
              description: "Target longitude"
            RADIUS_KM:
              type: "number"
              description: "Radius in kilometers"
          required:
            - TARGET_LAT
            - TARGET_LON
            - RADIUS_KM

  tool_resources:
    GLOBAL_QUAKE_LOGGING_TOOL:
      semantic_model_file: "@YUUBOT_DB.MODEL.EARTHQUAKE_STAGE/global_quake_logger.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "EARTHQUAKE_WH_XS"
    JP_QUAKE_LOGGING_TOOL:
      semantic_model_file: "@YUUBOT_DB.MODEL.EARTHQUAKE_STAGE/jp_quake_logger.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "EARTHQUAKE_WH_XS"
    TAVILY_SEARCH_TOOL:
      type: "procedure"
      execution_environment:
        type: "warehouse"
        warehouse: "EARTHQUAKE_WH_XS"
      identifier: "TAVILY_SEARCH_API.TAVILY_SCHEMA.TAVILY_WEB_SEARCH"
    FORECAST_EARTHQUAKE_PROB_TOOL:
      type: "function"
      execution_environment:
        type: "warehouse"
        warehouse: "EARTHQUAKE_WH_XS"
      identifier: "YUUBOT_DB.MODEL.FORECAST_EARTHQUAKE_PROB"
  $$;