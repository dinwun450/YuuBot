FROM python:3.7-alpine
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY yuuapp/ /app
WORKDIR /app

ENTRYPOINT ["python3"]
CMD ["yuubot_app.py"]