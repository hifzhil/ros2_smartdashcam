#!/bin/bash

cd /home/numby/jazzy_ws || { echo "Workspace not found!"; exit 1; }

echo "Building rdd_detector package..."
colcon build --packages-select rdd_detector

echo "Sourcing the setup file..."
source install/setup.bash

echo "Running rdd_detector node..."
ros2 run rdd_detector rdd_detector