#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from datetime import datetime, timezone
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
import message_filters
from cv_bridge import CvBridge
import cv2
import base64
import json
import numpy as np
from google.cloud import storage
import os
from ament_index_python.packages import get_package_share_directory
import yaml

from sensor_msgs.msg import Image, NavSatFix
from std_msgs.msg import String, Float64
from yolo_msgs.msg import Detection, DetectionArray

class AnomalyDetector(Node):
    def __init__(self):
        super().__init__('anomaly_detector')
        
        # Load config file
        self.load_config()
        
        # Initialize components
        self.bridge = CvBridge()
        self.latest_gps = None
        
        # State management
        self.is_car_moving = True
        self.needs_reset = False
        self.has_reset_counts = False
        
        # Tracking dictionaries
        self.tracked_objects = {}
        self.tracked_history = {}
        self.last_published_time = {}
        
        self.anomaly_config = {
            'balok_kayu': {
                'translation': 'wood_beam',
                'confidence': 0.2
            },
            'besi': {
                'translation': 'iron',
                'confidence': 0.2
            },
            'genangan': {
                'translation': 'puddle',
                'confidence': 0.2
            },
            'guardrail_hilang': {
                'translation': 'missing_guardrail',
                'confidence': 0.2
            },
            'guardrail_miring': {
                'translation': 'tilted_guardrail',
                'confidence': 0.2
            },
            'kendaraan_berhenti': {
                'translation': 'stopped_vehicle',
                'confidence': 0.25
            },
            'lubang': {
                'translation': 'pothole',
                'confidence': 0.1
            },
            'motor': {
                'translation': 'motorcycle',
                'confidence': 0.3
            },
            'orang_dipinggir_tol': {
                'translation': 'person_on_tollroad',
                'confidence': 0.4
            },
            'pecahan_ban': {
                'translation': 'tire_fragment',
                'confidence': 0.3
            },
            'pohon': {
                'translation': 'tree',
                'confidence': 0.3
            },
            'sampah_kardus': {
                'translation': 'cardboard_trash',
                'confidence': 0.2
            },
            'stickone_roboh': {
                'translation': 'fallen_stickcone',
                'confidence': 0.2
            },
            'retakan': {
                'translation': 'crack',
                'confidence': 0.2
            },
            'tanaman_rimbun': {
                'translation': 'dense_vegetation',
                'confidence': 0.2
            }
        }
        # Initialize GCS client if not in debug mode
        if not self.debug_mode:
            self._init_gcs()
        else:
            self.storage_client = None
            self.get_logger().info('Running in debug mode - GCS upload disabled')
        
        # Setup subscribers
        self._init_subscribers()
        
        # Setup publisher
        self.anomaly_publisher = self.create_publisher(
            String,
            '/smartdashcam/anomaly',
            10
        )
        
        self.get_logger().info('Anomaly detector initialized')

    def load_config(self):
        try:
            # Get the package share directory
            package_share_dir = get_package_share_directory('smartdashcam')
            config_file = os.path.join(package_share_dir, 'config', 'smartdashcam_config.yaml')
            
            self.get_logger().info(f'Attempting to load config from: {config_file}')
            
            # Try to read the YAML file directly to verify its contents
            yaml_content = None
            try:
                with open(config_file, 'r') as f:
                    yaml_content = yaml.safe_load(f)
                    self.get_logger().info('Raw YAML content for anomaly_detector:')
                    self.get_logger().info(str(yaml_content.get('anomaly_detector', {})))
            except Exception as e:
                self.get_logger().error(f'Error reading YAML file directly: {str(e)}')
                return

            # Get values from YAML or use fallbacks
            yaml_params = yaml_content.get('anomaly_detector', {}).get('ros__parameters', {})
            
            self.declare_parameters(
                namespace='anomaly_detector',
                parameters=[
                    ('ros__parameters.dashcam_id', yaml_params.get('dashcam_id', '000')),
                    ('ros__parameters.device_id', yaml_params.get('device_id', 'zil-msi')),
                    ('ros__parameters.ruas_id', yaml_params.get('ruas_id', '001')),
                    ('ros__parameters.timezone', yaml_params.get('timezone', 'UTC')),
                    ('ros__parameters.debug_mode', yaml_params.get('debug_mode', False)),
                    ('ros__parameters.velocity_threshold', yaml_params.get('velocity_threshold', 5.0)),
                    ('ros__parameters.time_threshold', yaml_params.get('time_threshold', 10.0)),
                    ('ros__parameters.image_width', yaml_params.get('image_width', 640)),
                    ('ros__parameters.image_height', yaml_params.get('image_height', 320)),
                    ('ros__parameters.gcs_bucket', yaml_params.get('gcs_bucket', 'dashcam-sinatra'))
                ]
            )
            
            # Get all parameters and assign them to class attributes
            self.dashcam_id = self.get_parameter('anomaly_detector.ros__parameters.dashcam_id').value
            self.device_id = self.get_parameter('anomaly_detector.ros__parameters.device_id').value
            self.ruas_id = self.get_parameter('anomaly_detector.ros__parameters.ruas_id').value
            self.timezone = self.get_parameter('anomaly_detector.ros__parameters.timezone').value
            self.debug_mode = self.get_parameter('anomaly_detector.ros__parameters.debug_mode').value
            self.velocity_threshold = self.get_parameter('anomaly_detector.ros__parameters.velocity_threshold').value
            self.time_threshold = self.get_parameter('anomaly_detector.ros__parameters.time_threshold').value
            self.image_width = self.get_parameter('anomaly_detector.ros__parameters.image_width').value
            self.image_height = self.get_parameter('anomaly_detector.ros__parameters.image_height').value
            self.gcs_bucket = self.get_parameter('anomaly_detector.ros__parameters.gcs_bucket').value
            
            # Log all loaded parameters
            self.get_logger().info('Loaded parameters:')
            self.get_logger().info(f'  - dashcam_id: {self.dashcam_id}')
            self.get_logger().info(f'  - device_id: {self.device_id}')
            self.get_logger().info(f'  - ruas_id: {self.ruas_id}')
            self.get_logger().info(f'  - timezone: {self.timezone}')
            self.get_logger().info(f'  - debug_mode: {self.debug_mode}')
            self.get_logger().info(f'  - velocity_threshold: {self.velocity_threshold}')
            self.get_logger().info(f'  - time_threshold: {self.time_threshold}')
            self.get_logger().info(f'  - image_width: {self.image_width}')
            self.get_logger().info(f'  - image_height: {self.image_height}')
            self.get_logger().info(f'  - gcs_bucket: {self.gcs_bucket}')
            
        except Exception as e:
            self.get_logger().error(f'Error in load_config: {str(e)}')
            self.dashcam_id = '003'
            self.device_id = 'raspi3'
            self.ruas_id = '001'
            self.timezone = 'UTC'
            self.debug_mode = False
            self.velocity_threshold = 5.0
            self.time_threshold = 10.0
            self.image_width = 640
            self.image_height = 320
            self.gcs_bucket = 'dashcam-sinatra'

    def _init_gcs(self):
        try:
            package_share_dir = get_package_share_directory('smartdashcam')
            sa_path = os.path.join(package_share_dir, 'config', 'sa.json')
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_path
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.gcs_bucket)
            self.get_logger().info(f'GCS client initialized using {sa_path}')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize GCS client: {str(e)}')
            self.storage_client = None

    def _init_subscribers(self):
        image_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            depth=1
        )
        
        self.image_sub = message_filters.Subscriber(
            self, Image, '/image', qos_profile=image_qos
        )
        
        self.tracking_sub = message_filters.Subscriber(
            self, DetectionArray, '/yolo/tracking', qos_profile=10
        )
        
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.image_sub, self.tracking_sub], 10, 0.5
        )
        self.ts.registerCallback(self.detection_callback)
        
        self.create_subscription(
            NavSatFix, '/fix', self.gps_callback, 10
        )
        
        self.create_subscription(
            Float64, '/velocity', self.velocity_callback, 10
        )

    def velocity_callback(self, msg: Float64) -> None:
        if msg.data > self.velocity_threshold:
            self.is_car_moving = True
            self.has_reset_counts = False
        else:
            self.is_car_moving = False
        
        # self.get_logger().info(f"Car moving state: {self.is_car_moving}")

    def gps_callback(self, msg: NavSatFix) -> None:
        self.latest_gps = msg

    def create_gps_data(self) -> dict:
        if not self.latest_gps:
            return {
                "timezone": "UTC",
                "date_time": datetime.now(timezone.utc).isoformat(),
                "latitude": 0.0,
                "longitude": 0.0,
                "altitude": " M",
                "true_north_heading": " degree",
                "magnetic_north_heading": " degree",
                "ground_speed": "0 Kn",
                "ground_speed_km": "0 Km/h"
            }
        
        return {
            "timezone": "UTC",
            "date_time": datetime.now(timezone.utc).isoformat(),
            "latitude": self.latest_gps.latitude,
            "longitude": self.latest_gps.longitude,
            "altitude": f"{self.latest_gps.altitude}M",
            "true_north_heading": " degree",
            "magnetic_north_heading": " degree",
            "ground_speed": "0 Kn",
            "ground_speed_km": "0 Km/h"
        }

    def upload_to_gcs(self, image_bytes, class_name):
        if self.debug_mode:
            self.get_logger().info(f'Debug mode: Skipping upload for {class_name}')
            return "debug_mode_no_upload"
            
        try:
            if not self.storage_client:
                return ""
            
            timestamp = datetime.now().strftime('%d-%m-%Y')
            filename = f"{timestamp}/{self.dashcam_id}-{class_name}-{int(datetime.now().timestamp())}.jpg"
            
            blob = self.bucket.blob(filename)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            
            self.get_logger().info(f'Uploaded image to GCS: {filename}')
            return filename
        except Exception as e:
            self.get_logger().error(f'Failed to upload to GCS: {str(e)}')
            return ""

    def detection_callback(self, img_msg: Image, tracking_msg: DetectionArray) -> None:
        try:
            cv_image = self.bridge.imgmsg_to_cv2(img_msg, "bgr8")
            for detection in tracking_msg.detections:
                if detection.class_name in self.anomaly_config:
                    self._process_anomaly(cv_image, detection)
                    
        except Exception as e:
            self.get_logger().error(f'Error processing detection: {str(e)}')

    def _process_anomaly(self, cv_image: np.ndarray, detection: Detection) -> None:
        try:
            class_name = detection.class_name
            current_time = datetime.now()
            confidence_threshold = self.anomaly_config[class_name]['confidence']
            if detection.score < confidence_threshold:
                self.get_logger().debug(f"Skipping {class_name} - Confidence {detection.score:.2f} below threshold {confidence_threshold}")
                return
            
            if class_name not in self.tracked_objects:
                self.tracked_objects[class_name] = {}
            
            if detection.id in self.tracked_history:
                self.get_logger().info(f"Skipping {class_name} - ID {detection.id} already tracked")
                return
                
            should_process = False
            if self.is_car_moving:
                should_process = True
            else:
                should_process = len(self.tracked_objects[class_name]) == 0
                
            if should_process:
                last_time = self.last_published_time.get(class_name)
                if last_time is None or (current_time - last_time).total_seconds() >= self.time_threshold:
                    self.tracked_objects[class_name][detection.id] = 1
                    self.tracked_history[detection.id] = class_name
                    self.last_published_time[class_name] = current_time
                    
                    image_annotated = cv_image.copy()
                    
                    x1 = int(detection.bbox.center.position.x - detection.bbox.size.x/2)
                    y1 = int(detection.bbox.center.position.y - detection.bbox.size.y/2)
                    x2 = int(detection.bbox.center.position.x + detection.bbox.size.x/2)
                    y2 = int(detection.bbox.center.position.y + detection.bbox.size.y/2)
                    
                    cv2.rectangle(image_annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(
                        image_annotated,
                        f"{class_name}",
                        (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2
                    )
                    
                    image_resized = cv2.resize(image_annotated, (self.image_width, self.image_height))
                    
                    _, buffer = cv2.imencode('.jpg', image_resized)
                    image_bytes = buffer.tobytes()
                    
                    # Get translated class name from unified config
                    translated_class = self.anomaly_config[class_name]['translation']
                    image_name = self.upload_to_gcs(image_bytes, translated_class)
                    # In debug mode, send image as base64 instead of GCS path
                    payload = {
                        "image_base64": base64.b64encode(image_bytes).decode() if self.debug_mode else "",
                        "image_name": image_name,
                        "is_uploaded": not self.debug_mode and bool(image_name),
                        "width": self.image_width,
                        "height": self.image_height,
                        "date_time": datetime.now(timezone.utc).isoformat(),
                        "type": translated_class,
                        "bounding_box": [float(x1), float(y1), float(x2), float(y2)],
                        "gps_data": self.create_gps_data(),
                        "dashcam_id": self.dashcam_id,
                        "device_id": self.device_id,
                        "ruas_id": self.ruas_id,
                        "timezone": self.timezone
                    }
                    
                    # Publish anomaly
                    msg = String()
                    msg.data = json.dumps(payload)
                    self.anomaly_publisher.publish(msg)
                    
                    self.get_logger().info(f'Published anomaly: {class_name} (ID: {detection.id})')
                else:
                    self.get_logger().info(f"Skipping {class_name} - Time threshold not met")
            else:
                self.get_logger().info(
                    f"Skipping {class_name} (ID: {detection.id}) - "
                    f"Car stopped and already tracking {len(self.tracked_objects[class_name])} instances"
                )
                
        except Exception as e:
            self.get_logger().error(f'Error processing anomaly: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = AnomalyDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()