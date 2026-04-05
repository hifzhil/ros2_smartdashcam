import os
import launch
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import yaml
from launch.actions import TimerAction, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable

def load_configurations():
    config_file_path = os.path.join(get_package_share_directory('smartdashcam'), 'config', 'gscam_pipeline.yaml')
    with open(config_file_path, 'r') as file:
        return yaml.safe_load(file)

def generate_launch_description():
    config = load_configurations()

    # Add camera info manually to the parameters
    gscam_params = config['gscam_publisher']['ros__parameters']
    
    # Get home directory from environment
    home_dir = os.path.expanduser('~')
    camera_info_path = os.path.join(home_dir, '.ros', 'camera_info', 'camera.yaml')
    
    # Make camera calibration optional
    if os.path.exists(camera_info_path):
        gscam_params.update({
            'camera_name': 'camera',
            'camera_info_url': f'file://{camera_info_path}',
            'use_camera_info': True
        })
    else:
        gscam_params.update({
            'camera_name': 'camera',
            'use_camera_info': False
        })

    # Set necessary environment variables
    env_vars = [
        SetEnvironmentVariable('GST_DEBUG', '2'),
        SetEnvironmentVariable('GST_DEBUG_DUMP_DOT_DIR', '/tmp/gst-dot'),
    ]

    # Add a delay before starting the node to ensure RTSP stream is ready
    return LaunchDescription(env_vars + [
        TimerAction(
            period=5.0,  # 5 second delay
            actions=[
                Node(
                    package='gscam',
                    executable='gscam_node',
                    name='camera',
                    namespace='',
                    output='screen',
                    parameters=[gscam_params],
                    remappings=[
                        ('camera/image_raw', '/image'),
                        ('camera_info', '/camera/camera_info'),
                        ('set_camera_info', '/camera/set_camera_info')
                    ],
                    respawn=True,
                    respawn_delay=2.0
                )
            ]
        )
    ])
