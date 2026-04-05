#!/bin/bash

SERVICE_DIR="/home/hifzhil/jazzy_ws/src/ros2_smartdashcam/service"
TIMER_DIR="/home/hifzhil/jazzy_ws/src/ros2_smartdashcam/service"
SYSTEMD_DIR="/etc/systemd/system"
SCRIPTS_DIR="/home/hifzhil/jazzy_ws/src/ros2_smartdashcam/script"

if [ ! -d "$SERVICE_DIR" ]; then
    echo "Service directory $SERVICE_DIR does not exist. Exiting."
    exit 1
fi

# Make all scripts executable
echo "Making scripts executable..."
for script in "$SCRIPTS_DIR"/*.sh; do
    if [ -f "$script" ]; then
        sudo chmod +x "$script"
        echo "Made $(basename "$script") executable."
    fi
done

# Clean up existing ROS2 services
echo "Checking for existing ROS2 services..."
existing_services=$(systemctl list-units --type=service --all | grep "ros2_" | awk '{print $1}')
existing_timers=$(systemctl list-units --type=timer --all | grep "ros2_" | awk '{print $1}')

if [ -n "$existing_services" ]; then
    echo "Found existing ROS2 services. Cleaning up..."
    
    while IFS= read -r service; do
        echo "Processing $service..."
        
        # Check if service is active before stopping
        if systemctl is-active --quiet "$service"; then
            echo "Stopping $service..."
            sudo systemctl stop "$service"
            sleep 1  # Give it a moment to stop
        else
            echo "$service is not active."
        fi
        
        # Check if service is enabled before disabling
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo "Disabling $service..."
            sudo systemctl disable "$service"
        else
            echo "$service is not enabled."
        fi
        
        # Remove the service file if it exists
        if [ -f "${SYSTEMD_DIR}/$service" ]; then
            echo "Removing $service file..."
            sudo rm "${SYSTEMD_DIR}/$service"
        fi
    done <<< "$existing_services"
fi

if [ -n "$existing_timers" ]; then
    echo "Found existing ROS2 timers. Cleaning up..."
    
    while IFS= read -r timer; do
        echo "Processing $timer..."
        
        # Check if timer is active before stopping
        if systemctl is-active --quiet "$timer"; then
            echo "Stopping $timer..."
            sudo systemctl stop "$timer"
            sleep 1  # Give it a moment to stop
        else
            echo "$timer is not active."
        fi
        
        # Check if timer is enabled before disabling
        if systemctl is-enabled --quiet "$timer" 2>/dev/null; then
            echo "Disabling $timer..."
            sudo systemctl disable "$timer"
        else
            echo "$timer is not enabled."
        fi
        
        # Remove the timer file if it exists
        if [ -f "${SYSTEMD_DIR}/$timer" ]; then
            echo "Removing $timer file..."
            sudo rm "${SYSTEMD_DIR}/$timer"
        fi
    done <<< "$existing_timers"
fi

# Reload systemd to recognize the changes
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sleep 2  # Give systemd a moment to process the changes

# Install new services
echo "Installing new services..."
for service_file in "$SERVICE_DIR"/*.service; do
    if [ -f "$service_file" ]; then
        sudo cp "$service_file" "$SYSTEMD_DIR"
        echo "Copied $(basename "$service_file") to $SYSTEMD_DIR."
        sudo systemctl enable "$(basename "$service_file")"
        echo "Enabled $(basename "$service_file")."
        sudo systemctl start "$(basename "$service_file")"
        echo "Started $(basename "$service_file")."
        sleep 1  # Give each service a moment to start
    fi
done

# Install new timers
echo "Installing new timers..."
for timer_file in "$TIMER_DIR"/*.timer; do
    if [ -f "$timer_file" ]; then
        sudo cp "$timer_file" "$SYSTEMD_DIR"
        echo "Copied $(basename "$timer_file") to $SYSTEMD_DIR."
        sudo systemctl enable "$(basename "$timer_file")"
        echo "Enabled $(basename "$timer_file")."
        sudo systemctl start "$(basename "$timer_file")"
        echo "Started $(basename "$timer_file")."
        sleep 1  # Give each timer a moment to start
    fi
done

sudo systemctl daemon-reload
echo "Final systemd daemon reload completed."

echo "All services and timers have been assigned and started."