# smartdashcam/launch/gps_bringup.launch.py
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_share_directory = get_package_share_directory('smartdashcam')
    config_file_path = os.path.join(package_share_directory, 'config', 'gps_config.yaml')

    return LaunchDescription([
        Node(
            package='nmea_navsat_driver',
            executable='nmea_serial_driver',
            name='gps_node',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB1',
                'baud': 115200,
                'frame_id': 'gps',
                'use_rtk': False
            }],
            respawn=True,
            respawn_delay=5.0
        )
    ])
