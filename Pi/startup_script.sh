#!/bin/bash

PROJECT_DIR="/home/zuhair/Desktop/Music_Player_Assistant/Pi"

cd "$PROJECT_DIR" || exit 1

echo "Starting music service..."
source venv/bin/activate
nohup python music.py > ~/music.log 2>&1 &
echo "Music service pid : ${!}"

echo "Starting voice server..."
nohup python server.py > ~/server.log 2>&1 &
echo "Voice server pid : ${!}"

sleep 1

echo "Starting C controller..."
gcc controller.c ./CustomLibs/LinkedList.c -o controller -pthread -lcjson
if [ $? -ne 0 ]; then
    echo "Controller compilation failed."
    exit 1
fi
nohup stdbuf -oL ./controller > ~/controller.log 2>&1 &
echo "C controller pid : ${!}"