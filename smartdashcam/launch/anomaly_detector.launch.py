#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get the package share directory
    pkg_share = get_package_share_directory('smartdashcam')

    # Create the config file path
    config_file = os.path.join(pkg_share, 'config', 'smartdashcam_config.yaml')

    return LaunchDescription([
        Node(
            package='smartdashcam',
            executable='anomaly_detector',
            name='anomaly_detector',
            parameters=[config_file],
            output='screen',
            emulate_tty=True
        )
    ])