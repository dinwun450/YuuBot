FROM python:3.9-alpine
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY yuuapp_chat/ /app
WORKDIR /app

EXPOSE 4092
HEALTHCHECK CMD curl --fail http://localhost:4092/_stcore/health

ENTRYPOINT ["streamlit", "run", "yuubot_chat_app.py", "--server.port=4092", "--server.address=0.0.0.0"]
