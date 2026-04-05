#!/bin/bash

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $BRANCH"

if [ "$BRANCH" == "main" ]; then
    ROS_DISTRO="jazzy"
    WORKSPACE="jazzy_ws"
    ROS_SOURCE="/opt/ros/jazzy/setup.bash"
elif [ "$BRANCH" == "staging/jazzy_ws" ]; then
    ROS_DISTRO="jazzy"
    WORKSPACE="jazzy_ws"
    ROS_SOURCE="/opt/ros/jazzy/setup.bash"
elif [ "$BRANCH" == "staging/humble" ]; then
    ROS_DISTRO="humble"
    WORKSPACE="humble_ws"
    ROS_SOURCE="/opt/ros/humble/setup.bash"
elif [ "$BRANCH" == "development" ]; then
    ROS_DISTRO="jazzy"
    WORKSPACE="jazzy_ws"
    ROS_SOURCE="/opt/ros/jazzy/setup.bash"
else
    echo "Unknown branch. Exiting."
    exit 1
fi

echo "ROS Distribution: $ROS_DISTRO"
echo "Workspace: $WORKSPACE"
echo "ROS Source: $ROS_SOURCE"

case "$(hostname)" in
    "raspi1")
        export DASHCAM_ID="001"
        USERNAME="pi"
        ;;
    "raspi2")
        export DASHCAM_ID="002"
        USERNAME="pi"
        ;;
    "raspi3")
        export DASHCAM_ID="003"
        USERNAME="pi"
        ;;
    "raspi4")
        export DASHCAM_ID="004"
        USERNAME="pi"
        ;;
    "raspi5")
        if [ "$ROS_DISTRO" == "jazzy" ]; then
            export DASHCAM_ID="005"
            USERNAME="pi"
        else
            echo "raspi5 is only configured for jazzy. Exiting."
            exit 1
        fi
        ;;
    "MSI")
        export DASHCAM_ID="000"
        USERNAME="hifzhil"
        ;;
    *)
        echo "Unknown device. Exiting."
        exit 1
        ;;
esac

echo "DASHCAM_ID: $DASHCAM_ID"

CONFIG_DIR="/home/$USERNAME/$WORKSPACE/src/ros2_smartdashcam/smartdashcam/config"
CONFIG_FILE="$CONFIG_DIR/smartdashcam_config.yaml"
DEFAULT_CONFIG_FILE="$CONFIG_DIR/smartdashcam_config_default.yaml"

echo "Config file path: $CONFIG_FILE"

if [ -f "$DEFAULT_CONFIG_FILE" ]; then
    cp "$DEFAULT_CONFIG_FILE" "$CONFIG_FILE"
    echo "Restored default configuration from $DEFAULT_CONFIG_FILE"
else
    echo "Default configuration file $DEFAULT_CONFIG_FILE does not exist. Exiting."
    exit 1
fi

sed -i "s/\${DASHCAM_ID}/$DASHCAM_ID/g" "$CONFIG_FILE"
sed -i "s/\${HOSTNAME}/$(hostname)/g" "$CONFIG_FILE"

echo "Sourcing ROS setup files..."
if [ ! -f "$ROS_SOURCE" ]; then
    echo "ROS source file does not exist. Exiting."
    exit 1
fi

source "$ROS_SOURCE"
if [ ! -f "/home/$USERNAME/$WORKSPACE/install/setup.bash" ]; then
    echo "Workspace setup file does not exist. Exiting."
    exit 1
fi

source "/home/$USERNAME/$WORKSPACE/install/setup.bash"

SCRIPTS_DIR="/home/$USERNAME/$WORKSPACE/src/ros2_smartdashcam/script"
SERVICES_DIR="/home/$USERNAME/$WORKSPACE/src/ros2_smartdashcam/service"

SCRIPTS=("start_ros_rdd.sh" "assign_services.sh" "configure_port.sh" "start_ros_gps.sh" "start_ros_web_video_server.sh" "start_ros_mqtt.sh" "start_ros_yolo.sh" "start_ros_gscam.sh" "start_ros_main.sh")
SERVICES=("start_ros_rdd.service" "ros2_gps.service" "ros2_main.service" "ros2_web_video_server.service" "ros2_mqtt.service" "ros2_yolo.service" "ros2_gscam.service")

for script in "${SCRIPTS[@]}"; do
    SCRIPT_PATH="$SCRIPTS_DIR/$script"
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "Script $SCRIPT_PATH does not exist. Skipping."
        continue
    fi
    echo "Updating script: $script"
    sed -i "s|/home/[^/]\+/[^/]\+|/home/$USERNAME/$WORKSPACE|g" "$SCRIPT_PATH"
    sed -i "s|/opt/ros/[^/]\+/setup.bash|$ROS_SOURCE|g" "$SCRIPT_PATH"
done

for service in "${SERVICES[@]}"; do
    SERVICE_PATH="$SERVICES_DIR/$service"
    if [ ! -f "$SERVICE_PATH" ]; then
        echo "Service $SERVICE_PATH does not exist. Skipping."
        continue
    fi
    echo "Updating service: $service"
    sed -i "s|/home/[^/]\+/[^/]\+|/home/$USERNAME/$WORKSPACE|g" "$SERVICE_PATH"
    sed -i "s|/opt/ros/[^/]\+/setup.bash|$ROS_SOURCE|g" "$SERVICE_PATH"
done

echo "Building the ROS 2 workspace..."
WORKSPACE_PATH="/home/$USERNAME/$WORKSPACE"
echo "Workspace path: $WORKSPACE_PATH"
if [ ! -d "$WORKSPACE_PATH" ]; then
    echo "Workspace directory does not exist. Exiting."
    exit 1
fi

cd "$WORKSPACE_PATH"
colcon build --packages-select smartdashcam yolo_smartdashcam rdd_detector

if [ -f "$DEFAULT_CONFIG_FILE" ]; then
    cp "$DEFAULT_CONFIG_FILE" "$CONFIG_FILE"
    echo "Restored default configuration to $CONFIG_FILE after build"
else
    echo "Default configuration file $DEFAULT_CONFIG_FILE does not exist. Exiting."
    exit 1
fi

cd "/home/$USERNAME/$WORKSPACE/src/ros2_smartdashcam"
source "/home/$USERNAME/$WORKSPACE/install/setup.bash"
echo "Build completed successfully."