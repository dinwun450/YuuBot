import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from data.langchain_tools_jpearthquakes import get_earthquake_data, get_earthquake_data_by_date, get_earthquake_data_by_magnitude, get_earthquake_data_by_intensity, count_earthquakes, filter_earthquakes_by_two_or_more_factors
from langgraph.prebuilt import create_react_agent

st.set_page_config(page_title="YuuBot Chat 1.0 (Beta)", page_icon="🐸", layout="wide")
st.title("YuuBot Chat 1.0 (Beta)")
gapi_key = st.text_input("Enter your Google API Key:", type="password")

# Initialize the chat model
def generate_response(prompt):
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=gapi_key
    )

    agent_executor = create_react_agent(model, [
        get_earthquake_data, 
        count_earthquakes,
        get_earthquake_data_by_date, 
        get_earthquake_data_by_magnitude, 
        get_earthquake_data_by_intensity, 
        filter_earthquakes_by_two_or_more_factors
    ])

    st.info(agent_executor.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        stream_mode="values",
    )["messages"][-1].content)

# Streamlit app layout
with st.form("chat_form"):
    text = st.text_input("Enter your question:")
    submit_button = st.form_submit_button("Send")

    if submit_button and text:
        if gapi_key:
            try:
                generate_response(text)
            except Exception as e:
                st.error(f"An error occurred: {e}", icon="🚨")
        else:
            st.error("Please enter a valid Google API Key.", icon="🚨")

# Some text
st.write("Note: YuuBot Chat is under development, as some features (tools) are not yet implemented. Stay tuned for updates!")