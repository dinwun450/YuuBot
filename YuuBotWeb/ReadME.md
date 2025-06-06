# Instructions for Running YuuBot Web

## Prerequisites
* Docker Desktop App on Windows, Linux, or MacOS. For installation, see [Docker Website](https://www.docker.com/get-started/) for details.

## Steps
1. On the `YuuBotWeb` folder, run:
   ```
   docker-compose up -d
   ```
2. Wait for a few minutes, then run:
   ```
   docker exec -it scylla-node-mirai cqlsh
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
     PRIMARY KEY((date, epicenter, magnitude, shindo)));
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
   docker run -d --net=yuubot_web -p 4092:4092 --name <any container name> <build name> yuubot_app.py
   ```
   Where `<any container name>` represents the name of the container you're running, and `<build name>` indicates the build you have created in step four.
5. View your running app in localhost:4092.

## Notes
* You can check your status of each node from `docker-compose` using:
  ```
  docker exec -it <any of three nodes> nodetool status
  ```
  Where `<any of three nodes>` can be replaced by `scylla-node-mirai`, `scylla-node-yuuki`, or `scylla-node-yuuki`.
* If any of the three nodes displayed an error or a "DN" after successfully running the nodetool status in the command above, try running:
  ```
  docker stop $(docker ps -aq)
  docker rm $(docker ps -aq)
  ```
  After that, try running the commands as described in the steps section above.
* For Step 2 in the Steps section, you can replace `scylla-node-mirai` with `scylla-node-yuuki` or `scylla-node-mari` for initializing the table and keyspace.
