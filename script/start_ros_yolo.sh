#!/bin/bash

source /opt/ros/jazzy/setup.bash
source /home/hifzhil/jazzy_ws/install/setup.bash

echo "Launching YOLOv8 node..."
ros2 launch smartdashcam yolov8.launch.py 