#!/bin/bash

# Wait for WiFi connection
echo "Checking WiFi connection..."
while ! nmcli -t -f ACTIVE,SSID dev wifi | grep -q '^yes'; do
    echo "Waiting for Wi-Fi connection..."
    sleep 5
done

sleep 5

echo "WiFi connected!"

source /opt/ros/jazzy/setup.bash
source /home/hifzhil/jazzy_ws/install/setup.bash

echo "Launching gscam node..."
ros2 launch smartdashcam gscam.launch.py 