import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='web_video_server',
            executable='web_video_server',
            name='web_video_server',
            output='screen',
            parameters=[{
                'port': 8080,
                'address': '0.0.0.0',
                'server_threads': 10,
                'ros_threads': 4
            }],
            respawn=True,
            respawn_delay=2.0
        )
    ])