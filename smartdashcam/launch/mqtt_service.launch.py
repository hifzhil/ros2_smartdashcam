import os
import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def load_configurations():
    config_file_path = os.path.join(get_package_share_directory('smartdashcam'), 'config', 'smartdashcam_config.yaml')
    with open(config_file_path, 'r') as file:
        return yaml.safe_load(file)

def generate_launch_description():
    config = load_configurations()
    mqtt_config = config['mqtt']['ros__parameters']
    dashcam_id = mqtt_config['dashcam_id']

    package_share_directory = get_package_share_directory('smartdashcam')
    # ca_certificate_path = os.path.join(package_share_directory, 'config', '.crt', 'ca.crt')
    # client_certificate_path = os.path.join(package_share_directory, 'config', '.crt', 'client.crt')
    # client_key_path = os.path.join(package_share_directory, 'config', '.crt', 'client.key')
    # mqtt_client offline message buffer (stores messages when disconnected)
    buffer_directory = os.path.join(package_share_directory, 'buffer')

    broker = mqtt_config['broker']
    broker_params = {
        'host': broker['host'],
        'port': broker['port'],
        # 'user': broker.get('user'),
        # 'pass': broker.get('pass'),
        # 'tls': {
        #     'enabled': True,
        #     'ca_certificate': ca_certificate_path,
        # }
        'tls': {'enabled': False}
    }

    return LaunchDescription([
        DeclareLaunchArgument('dashcam_id', default_value=dashcam_id),
        Node(
            package='mqtt_client',
            executable='mqtt_client',
            name='mqtt_client',
            output='screen',
            parameters=[{
                'broker': broker_params,
                'client': {
                    'id': dashcam_id,
                    'buffer': {
                        'size': 10,
                        'directory': buffer_directory
                    },
                    # 'tls': {
                    #     'certificate': client_certificate_path,
                    #     'key': client_key_path,
                    #     'password': "",
                    #     'version': "",
                    #     'verify': True,
                    #     'alpn_protos': ""
                    # }
                    'last_will': {
                        'topic': "last_will_topic",
                        'message': "offline",
                        'qos': 0,
                        'retained': False
                    },
                    'clean_session': True,
                    'keep_alive_interval': 60.0,
                    'max_inflight': 65535
                },
                'bridge': {
                    'ros2mqtt': {
                        'ros_topics': [
                            '/ping/primitive',
                            '/smartdashcam/gps',
                            '/smartdashcam/vision',
                            '/smartdashcam/anomaly',
                            '/smartdashcam/debug_counter',
                            '/smartdashcam/heartbeat'
                        ],
                        '/smartdashcam/gps': {
                            'mqtt_topic': f"DashCam/log-trip/{dashcam_id}",
                            'primitive': True,
                            'ros_type': 'std_msgs/msg/String',
                            'advanced': {
                                'ros': {
                                    'queue_size': 10,
                                    'qos': {
                                        'durability': 'auto',
                                        'reliability': 'auto'
                                    }
                                }
                            }
                        },
                        '/smartdashcam/vision': {
                            'mqtt_topic': f"DashCam/log-vision/{dashcam_id}",
                            'primitive': True,
                            'ros_type': 'std_msgs/msg/String',
                            'advanced': {
                                'ros': {
                                    'queue_size': 10,
                                    'qos': {
                                        'durability': 'auto',
                                        'reliability': 'auto'
                                    }
                                }
                            }
                        },
                        '/smartdashcam/anomaly': {
                            'mqtt_topic': f"DashCam/log-vision-anomaly/{dashcam_id}",
                            'primitive': True,
                            'ros_type': 'std_msgs/msg/String',
                            'advanced': {
                                'ros': {
                                    'queue_size': 10,
                                    'qos': {
                                        'durability': 'auto',
                                        'reliability': 'auto'
                                    }
                                }
                            }
                        },
                        '/smartdashcam/debug_counter': {
                            'mqtt_topic': f"DashCam/debug-counter/{dashcam_id}",
                            'primitive': True,
                            'ros_type': 'std_msgs/msg/String',
                            'advanced': {
                                'ros': {
                                    'queue_size': 10,
                                    'qos': {
                                        'durability': 'auto',
                                        'reliability': 'auto'
                                    }
                                }
                            }
                        },
                        '/smartdashcam/heartbeat': {
                            'mqtt_topic': f"DashCam/log-heartbeat/{dashcam_id}",
                            'primitive': True,
                            'ros_type': 'std_msgs/msg/String',
                            'advanced': {
                                'ros': {
                                    'queue_size': 10,
                                    'qos': {
                                        'durability': 'auto',
                                        'reliability': 'auto'
                                    }
                                }
                            }
                        }
                    }
                }
            }]
        )
    ])