import os
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    yolo_bringup_dir = get_package_share_directory("yolo_bringup")
    model_path = os.path.join(get_package_share_directory('smartdashcam'), 'config', 'model', "your_model.pt")

    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(yolo_bringup_dir, "launch", "yolo.launch.py")
                ),
                launch_arguments={
                    "model": LaunchConfiguration("model", default=model_path),
                    "tracker": LaunchConfiguration("tracker", default="bytetrack.yaml"),
                    "device": LaunchConfiguration("device", default="cpu"),
                    "enable": LaunchConfiguration("enable", default="True"),
                    "threshold": LaunchConfiguration("threshold", default="0.1"),
                    "imgsz_height": LaunchConfiguration("imgsz_height", default="416"),
                    "imgsz_width": LaunchConfiguration("imgsz_width", default="416"),
                    "use_debug": LaunchConfiguration("use_debug", default="False"),
                    "input_image_topic": LaunchConfiguration(
                        "input_image_topic", default="/image"
                    ),
                    "image_reliability": LaunchConfiguration(
                        "image_reliability", default="2"
                    ),
                    "namespace": LaunchConfiguration("namespace", default="yolo"),
                }.items(),
            ),
            Node(
                package='yolo_smartdashcam',
                executable='debug_node',
                name='debug_node',
                namespace='yolo',
                parameters=[{
                    "image_reliability": LaunchConfiguration(
                        "image_reliability", default="2"
                    ),
                }],
                remappings=[
                    ("image_raw", "/image"),
                    ("detections", "tracking"),
                ],
            )
        ]
    ) 