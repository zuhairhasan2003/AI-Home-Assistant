#!/bin/bash

echo "Stopping Home AI Assistant..."

pkill -f "python server.py"
pkill -f "python music.py"
pkill -x controller
pkill -x lights

echo "All services stopped."