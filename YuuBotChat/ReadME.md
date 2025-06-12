# Instructions for Running YuuBot Chat

## Prerequisites
* Docker Desktop App on Windows, Linux, or MacOS. For installation, see [Docker Website](https://www.docker.com/get-started/) for details.

## Steps
1. On the `YuuBotWeb` folder, run:
   ```
   docker-compose up -d
   ```
2. Wait for a few minutes, then run:
   ```
   docker exec -it scylla-node-one cqlsh
   ```
   * Inside the Cqlsh shell, run:
     ```
     CREATE KEYSPACE earthquakes WITH REPLICATION = { 'class' : 'NetworkTopologyStrategy','DC1' : 3};

     USE earthquakes;
    
     CREATE TABLE earthquake_data (
     date text,
     epicenter text, 
     magnitude text, 
     shindo text,
     PRIMARY KEY((date, time, epicenter, magnitude, shindo)));
     ```
   * Exit the Cqlsh shell by running:
     ```
     exit
     ```
3. Create a build by running:
   ```
   docker build -t <any name> .
   ```
   Where `<any name>` represents the name of the build you're about to create.
4. Run your build with:
   ```
   docker run -d --net=yuubotchat_web -p 4092:4092 --name <any container name> <build name>
   ```
   Where `<any container name>` represents the name of the container you're running, and `<build name>` indicates the build you have created in step four.
5. View your running app in localhost:4092.
   Where `<any container name>` indicates the container you're going to name before running it, and `<build name>` represents the build name you defined in step one.

## Notes
* To use the YuuBot Chatbot, grab your API key via [Google AI Studio](https://aistudio.google.com/apikey)
* See YuuBotWeb's ReadME for details, they're nearly the same.
