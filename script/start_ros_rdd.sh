#!/bin/bash

echo "Launching ROS 2 RDD Detector"
source /opt/ros/jazzy/setup.bash
source /home/hifzhil/jazzy_ws/install/setup.bash
ros2 launch smartdashcam rdd_detector.launch.py
