# Instructions for Running YuuBot Chat

## Prerequisites
* Docker Desktop App on Windows, Linux, or MacOS. For installation, see [Docker Website](https://www.docker.com/get-started/) for details.

## Steps
1. In the YuuBotChat directory, run:
   ```
   docker build -t <any name> .
   ```
   Where `<any name>` represents the build you will name before running this command.
2. To start using your chatbot app, use:
   ```
   docker run -p 8501:8501 --name <any container name> <build name>
   ```
   Where `<any container name>` indicates the container you're going to name before running it, and `<build name>` represents the build name you defined in step one.

## Notes
* To use the YuuBot Chatbot, grab your API key via [Google AI Studio](https://aistudio.google.com/apikey)
