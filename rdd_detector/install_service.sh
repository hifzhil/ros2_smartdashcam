#!/bin/bash

# Get the current username
USERNAME=$(whoami)

# Replace placeholders in the service file
sed -i "s/YOUR_USERNAME/$USERNAME/g" rdd_detector.service

# Copy the service file to systemd directory
sudo cp rdd_detector.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable rdd_detector.service

echo "RDD Detector service has been installed and enabled."
echo "To start the service: sudo systemctl start rdd_detector.service"
echo "To check status: sudo systemctl status rdd_detector.service"
echo "To stop the service: sudo systemctl stop rdd_detector.service" 