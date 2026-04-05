#!/bin/bash
GPS_DEVICE="/dev/ttyUSB1"

if [ -e "$GPS_DEVICE" ]; then
    echo "GPS device detected at $GPS_DEVICE. Launching ROS 2 GPS application..."
    source /opt/ros/jazzy/setup.bash
    source /home/hifzhil/jazzy_ws/install/setup.bash
    ros2 launch smartdashcam gps_bringup.launch.py
else
    echo "No GPS device detected at $GPS_DEVICE. Exiting."
    exit 1
fi
