import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from data.jp_earthquakes_extractor_chat import get_earthquake_data
from data.date_of_earthquakes import extract_date
from cassandra.cluster import Cluster
from cassandra import ConsistencyLevel

class YuuBotChat:
    def __init__(self):
        self.cluster = Cluster(contact_points=["scylla-node-one", "scylla-node-two", "scylla-node-three"])
        self.session = self.cluster.connect(keyspace="earthquakes")
        self.session.default_consistency_level = ConsistencyLevel.QUORUM
        self.create_earthquake_table()

    def create_earthquake_table(self):
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS earthquake_data (
                date TEXT,
                time TEXT,
                epicenter TEXT,
                magnitude FLOAT,
                shindo TEXT,
                PRIMARY KEY (date, time, epicenter, magnitude, shindo)
            )
        """)

    def show_earthquake_data(self):
        result = self.session.execute(query="SELECT * FROM earthquake_data")
        return sorted(result, key=extract_date, reverse=True)
    
    def show_most_recent_earthquake(self):
        result = self.session.execute(query="SELECT * FROM earthquake_data")
        rows = list(result)
        if rows:
            most_recent = sorted(rows, key=lambda x: x.date, reverse=True)[0]
            return most_recent
        else:
            return "No earthquake data found."
        
    def show_earthquake_count(self):
        result = self.session.execute(query="SELECT COUNT(*) FROM earthquake_data")
        count = result.one()[0]
        return count
    
    def show_earthquake_data_by_any_field(self, field, value):
        try:
            query = f"SELECT * FROM earthquake_data WHERE {field} = %s ALLOW FILTERING"
            result = self.session.execute(query, (value,))
            rows = list(result)
            if rows:
                return sorted(rows, key=extract_date, reverse=True)
            else:
                return "No earthquake data found for the specified field."
        except Exception as e:
            return f"Error fetching data: {str(e)}"
        
    def count_earthquakes_by_any_field(self, field, value):
        try:
            if type(value) is str:
                query = f"SELECT COUNT(*) FROM earthquake_data WHERE {field} = %s ALLOW FILTERING"
                result = self.session.execute(query, (value,))
                count = result.one()[0]
            elif type(value) is float:
                query = f"SELECT COUNT(*) FROM earthquake_data WHERE {field} >= %s ALLOW FILTERING"
                result = self.session.execute(query, (value,))
                count = result.one()[0]
            return count
        except Exception as e:
            return f"Error counting earthquakes: {str(e)}"
    
    def add_earthquake(self, date, time, epicenter, magnitude, shindo):
        self.session.execute(
            "INSERT INTO earthquake_data (date, time, epicenter, magnitude, shindo) VALUES (%s, %s, %s, %s, %s)",
            (date, time, epicenter, magnitude, shindo)
        )

    def delete_all_earthquakes(self):
        self.session.execute("DROP TABLE IF EXISTS earthquake_data")
    
    def refresh_earthquake_data(self):
        self.delete_all_earthquakes()
        self.create_earthquake_table()
        earthquake_data = get_earthquake_data()

        for data in earthquake_data:
            self.add_earthquake(data["date"], data["time"], data["epicenter"], data["mag"], data["intensity"])

    def stop(self):
        self.cluster.shutdown()

yuuapp = YuuBotChat()
earthquake_data = get_earthquake_data()
for data in earthquake_data:
    yuuapp.add_earthquake(data["date"], data["time"], data["epicenter"], data["mag"], data["intensity"])

@tool
def show_earthquake_data() -> list:
    """
    Fetches all earthquake data from the database.
    Returns a list of dictionaries containing earthquake details.
    """
    return yuuapp.show_earthquake_data()

@tool
def show_most_recent_earthquake() -> dict:
    """
    Fetches the most recent earthquake data from the database.
    Returns a dictionary containing details of the most recent earthquake.
    """
    return yuuapp.show_most_recent_earthquake()

@tool
def show_earthquake_count() -> int:
    """
    Counts the total number of earthquakes recorded in the database.
    Returns the total count of earthquakes as an integer.
    """
    return yuuapp.show_earthquake_count()

@tool
def show_earthquake_data_by_date(date: str) -> list:
    """
    Fetches earthquake data for a specific date.
    :param date: The date in the format 'YYYY-MM-DD'.
    Returns a list of dictionaries containing earthquake details for that date.
    """
    return yuuapp.show_earthquake_data_by_any_field("date", date)

@tool
def show_earthquake_data_by_time(time: str) -> list:
    """
    Fetches earthquake data for a specific time.
    :param time: The time in the format 'HH:MM'.
    Returns a list of dictionaries containing earthquake details for that time.
    """
    return yuuapp.show_earthquake_data_by_any_field("time", time)

@tool
def show_earthquake_data_by_epicenter(epicenter: str) -> list:
    """
    Fetches earthquake data for a specific epicenter.
    :param epicenter: The epicenter of the earthquake.
    Returns a list of dictionaries containing earthquake details for that epicenter.
    """
    return yuuapp.show_earthquake_data_by_any_field("epicenter", epicenter)

@tool
def show_earthquake_data_by_magnitude(magnitude: str) -> list:
    """
    Fetches earthquake data for earthquakes with a magnitude greater than or equal to the specified value.
    :param magnitude: The minimum magnitude of the earthquake.
    Returns a list of dictionaries containing earthquake details for that magnitude.
    """
    magnitude = float(magnitude)  # Ensure magnitude is a float
    if magnitude < 0:
        raise ValueError("Magnitude must be a non-negative number.")
    return yuuapp.show_earthquake_data_by_any_field("magnitude", magnitude)

@tool
def show_earthquake_data_by_shindo(shindo: str) -> list:
    """
    Fetches earthquake data for a specific shindo (intensity).
    :param shindo: The intensity of the earthquake.
    Returns a list of dictionaries containing earthquake details for that shindo.
    """
    return yuuapp.show_earthquake_data_by_any_field("shindo", shindo)

@tool
def count_earthquakes_by_any_field(field: str, value: str) -> int:
    """
    Counts the number of earthquakes by a specific field and value.
    :param field: The field to filter by (e.g., 'date', 'epicenter', 'magnitude', 'shindo').
    :param value: The value to filter by.
    Returns the count of earthquakes as an integer.
    """
    return yuuapp.count_earthquakes_by_any_field(field, value)

@tool
def refresh_earthquake_data() -> str:
    """
    Refreshes the earthquake data by deleting the existing table and recreating it.
    Fetches new earthquake data from the source and populates the database.
    Returns a confirmation message.
    """
    yuuapp.refresh_earthquake_data()
    return "Earthquake data has been refreshed successfully."

st.set_page_config(page_title="YuuBot Chat", page_icon="🐸", layout="wide")
with st.sidebar:
    st.title("YuuBot Chat")
    gapi_key = st.text_input("Enter your Google API Key:", type="password")
    st.write("Note: YuuBot Chat is under development, as some features (tools) are not yet implemented. Stay tuned for updates! Also, please note that the LLMs given may hallucinate.")

if gapi_key:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gapi_key)
    agent = create_react_agent(llm, tools=[show_earthquake_data, show_most_recent_earthquake, show_earthquake_count,
                                           show_earthquake_data_by_date, show_earthquake_data_by_time, 
                                           show_earthquake_data_by_epicenter, show_earthquake_data_by_magnitude, 
                                           show_earthquake_data_by_shindo, count_earthquakes_by_any_field, refresh_earthquake_data])
    
    # Initialize messages in session_state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not gapi_key:
        st.warning("Please enter your Google API Key to use YuuBot Chat.")
    else:
        if prompt := st.chat_input(disabled=not gapi_key):
            st.session_state.messages.append(HumanMessage(content=prompt))
            with st.chat_message("user"):
                st.write(prompt)
            
            response = agent.invoke({"messages": st.session_state.messages}, stream_mode="values")["messages"][-1]
            st.session_state.messages.append(response)
            
            with st.chat_message("assistant"):
                st.write(response.content)
