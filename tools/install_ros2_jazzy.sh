#!/bin/bash

# Function to check if a command was successful
check_error() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        exit 1
    fi
}

# Print header
echo "=== ROS2 Jazzy Installation Script ==="
echo "This script will install ROS2 Jazzy and set up your workspace"

# Install ROS2 Jazzy
echo "Installing ROS2 Jazzy..."
sudo apt update && sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-jazzy-ros-base  install ros-dev-tools
check_error "Failed to install ROS2 Jazzy"

# Install system dependencies
echo "Installing GStreamer and system dependencies..."
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libjpeg-dev \
    zlib1g-dev \
    nlohmann-json3-dev \
    python3-opencv \
    python3-pip \
    python3-venv
check_error "Failed to install system dependencies"

# Install ROS 2 specific packages
echo "Installing ROS 2 specific packages..."
sudo apt install -y \
    ros-jazzy-cv-bridge \
    ros-jazzy-vision-opencv \
    ros-jazzy-image-transport \
    ros-jazzy-image-transport-plugins
check_error "Failed to install ROS 2 specific packages"

# Install Python packages
echo "Installing Python packages..."
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install --break-system-packages \
    "ultralytics>=8.0.0" \
    "tensorflow>=2.13.0" \
    "lapx>=0.5.4" \
    "google-cloud-storage>=2.10.0" \
    "transforms3d>=0.4.1"
check_error "Failed to install Python packages"

# Create workspace directory
echo "Creating workspace directory..."
mkdir -p ~/jazzy_ws/src
cd ~/jazzy_ws/src || exit 1

# Clone the repository
echo "Cloning ros2_smartdashcam repository..."
echo "Please enter your GitHub credentials when prompted..."
git clone https://github.com/hifzhil/ros2_smartdashcam.git
check_error "Failed to clone repository"

# Initialize and update submodules
cd ros2_smartdashcam || exit 1
git submodule init
check_error "Failed to initialize submodules"
git submodule update
check_error "Failed to update submodules"

# Source ROS2 environment
echo "Sourcing ROS2 environment..."
source /opt/ros/jazzy/setup.bash

# Initialize rosdep
echo "Initializing and updating rosdep..."
sudo rosdep init || true  # May fail if already initialized, that's OK
rosdep update
check_error "Failed to update rosdep"

# Install dependencies
cd ~/jazzy_ws || exit 1
rosdep install --from-path src --ignore-src -y
check_error "Failed to install dependencies"

# Build specific packages
echo "Building specific packages..."
colcon build --packages-select yolo_mshs smartdashcam_msgs
check_error "Failed to build specific packages"

# Source the workspace
source install/setup.bash

# Full build
echo "Performing full build..."
colcon build
check_error "Failed to perform full build"

# Final source
source install/setup.bash

echo "=== Installation Complete! ==="
echo "Please add the following line to your ~/.bashrc file to source ROS2 environment automatically:"
echo "source ~/jazzy_ws/install/setup.bash"

# Make the current shell source the workspace
exec bash 