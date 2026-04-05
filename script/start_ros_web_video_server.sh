#!/bin/bash

echo "Launching ROS 2 Web Video Server..."
source /opt/ros/jazzy/setup.bash
source /home/hifzhil/jazzy_ws/install/setup.bash
ros2 launch smartdashcam web_video_server.launch.py
