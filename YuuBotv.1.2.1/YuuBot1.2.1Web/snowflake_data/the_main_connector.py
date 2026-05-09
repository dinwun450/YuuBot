import snowflake.connector

def create_snowflake_connection(schema):
    """
    Create and return a Snowflake connection object.

    Parameters:
    schema (str): The schema to connect to.

    Returns:
    snowflake.connector.connection.SnowflakeConnection: A Snowflake connection object.
    """

    # Create a Snowflake connection
    try:
        conn = snowflake.connector.connect(
            user="[INSERT USERNAME HERE]",
            password="[INSERT PASSWORD HERE]",
            account="[INSERT ACCOUNT HERE]",
            warehouse="EARTHQUAKE_WH_XS",
            database="YUUBOT_DB",
            schema=schema
        )
        
        return conn
    except snowflake.connector.Error as e:
        print(f"Error connecting to Snowflake: {e}")
        return None
