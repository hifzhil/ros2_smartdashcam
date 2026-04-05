#!/bin/bash

check_port() {
    local port=$1
    if [ -c "$port" ]; then
        echo "$port is available."
        return 0
    else
        echo "$port is not available."
        return 1
    fi
}

test_baud_rate() {
    local port=$1
    local baud_rate=$2

    if stty -F "$port" "$baud_rate" 2>/dev/null; then
        echo "Successfully set baud rate $baud_rate on $port."
        return 0
    else
        echo "Failed to set baud rate $baud_rate on $port."
        return 1
    fi
}

SERIAL_PORTS=("/dev/ttyUSB1" "/dev/ttyUSB5")
BAUD_RATES=(9600 115200)

GPS_CONFIG_FILE="/home/hifzhil/jazzy_ws/src/ros2_smartdashcam/smartdashcam/config/gps_config.yaml"

available_port=""
available_baud=""

for port in "${SERIAL_PORTS[@]}"; do
    if check_port "$port"; then
        for baud in "${BAUD_RATES[@]}"; do
            if test_baud_rate "$port" "$baud"; then
                available_port="$port"
                available_baud="$baud"
                break 2
            fi
        done
    fi
done

if [ -n "$available_port" ] && [ -n "$available_baud" ]; then
    echo "Configuring GPS with port: $available_port and baud rate: $available_baud"
    sed -i "s/\${GPS_PORT}/$available_port/g" "$GPS_CONFIG_FILE"
    sed -i "s/\${BAUD_RATE}/$available_baud/g" "$GPS_CONFIG_FILE"
    echo "GPS configuration updated successfully."
else
    echo "No available serial port with a valid baud rate found."
    exit 1
fi