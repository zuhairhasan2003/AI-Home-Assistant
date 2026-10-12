#!/bin/bash

PROJECT_DIR="/home/zuhair/Desktop/Music_Player_Assistant/Client"

cd "$PROJECT_DIR" || exit 1

echo "Starting client/webpage server..."
nohup python server.py > /tmp/webpage_server.log 2>&1 &
echo "client/webpage server pid : ${!}"