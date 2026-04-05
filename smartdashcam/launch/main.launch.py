from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('smartdashcam')
    
    gps_bringup_launch = os.path.join(pkg_share, 'launch', 'gps_bringup.launch.py')
    gscam_launch = os.path.join(pkg_share, 'launch', 'gscam.launch.py')
    mqtt_service_launch = os.path.join(pkg_share, 'launch', 'mqtt_service.launch.py')
    yolov8_launch = os.path.join(pkg_share, 'launch', 'yolov8.launch.py')
    
    config_file = os.path.join(pkg_share, 'config', 'smartdashcam_config.yaml')

    return LaunchDescription([
        Node(
            package='smartdashcam',
            executable='smartdashcam_main',
            name='smartdashcam_main',
            output='screen',
            respawn=True,
            respawn_delay=2.0
        ),
        Node(
            package='smartdashcam',
            executable='anomaly_detector',
            name='anomaly_detector',
            parameters=[config_file],
            output='screen',
            emulate_tty=True
        )
    ])
