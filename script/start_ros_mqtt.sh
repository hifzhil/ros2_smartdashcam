#!/bin/bash

source /opt/ros/jazzy/setup.bash
source /home/hifzhil/jazzy_ws/install/setup.bash

echo "Launching MQTT service node..."
ros2 launch smartdashcam mqtt_service.launch.py 