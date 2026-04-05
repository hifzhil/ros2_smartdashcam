#!/usr/bin/env python3

import cv2
import numpy as np
from cv_bridge import CvBridge
import rclpy
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn, State
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
import message_filters
from typing import Tuple, Dict, List
import os
from skimage.feature import graycomatrix, graycoprops
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from keras.models import load_model
from ament_index_python.packages import get_package_share_directory

class EnhancedRoadDamageDetector(LifecycleNode):
    def __init__(self) -> None:
        super().__init__('rdd_detector')
        
        # Keep all your enhanced parameters
        self.declare_parameter('blur_kernel', 5)
        self.declare_parameter('canny_low', 100)
        self.declare_parameter('canny_high', 150)
        self.declare_parameter('roi_top_ratio', 0.3)
        self.declare_parameter('min_area', 50)
        self.declare_parameter('max_area', 40000)
        self.declare_parameter('min_confidence', 0.2)
        self.declare_parameter('image_reliability', QoSReliabilityPolicy.BEST_EFFORT)
        self.declare_parameter('roi_x1', 0.4)
        self.declare_parameter('roi_y1', 0.6)
        self.declare_parameter('roi_x2', 0.6)
        self.declare_parameter('roi_y2', 0.9)
        
        # Enhanced parameters
        self.declare_parameter('temporal_window_size', 5)
        self.declare_parameter('cnn_weight', 0.6)
        self.declare_parameter('opencv_weight', 0.4)
        self.declare_parameter('texture_weight', 0.3)
        self.declare_parameter('shape_weight', 0.7)
        
        # New parameters
        self.declare_parameter('min_circularity', 0.5)
        self.declare_parameter('min_solidity', 0.6)
        self.declare_parameter('min_contrast', 0.6)
        self.declare_parameter('max_aspect_ratio', 1.5)
        self.declare_parameter('min_aspect_ratio', 0.7)
        
        self.cv_bridge = CvBridge()
        self.prediction_history = []
        
        # Force CPU usage
        tf.config.set_visible_devices([], 'GPU')
        
        # Load CNN model
        self._load_model()
        
        # Initialize publishers
        self._init_publishers()

    def _load_model(self):
        """Load and initialize CNN model"""
        try:
            model_path = os.path.join(
                get_package_share_directory('smartdashcam'),
                'config',
                'model',
                'full_model.h5'
            )
            self.size = 300
            self.model = load_model(model_path)
            self.get_logger().info('Model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'Error loading model: {str(e)}')

    def _init_publishers(self):
        """Initialize all publishers"""
        self._roi_pub = self.create_publisher(Image, 'rdd/roi', 10)
        self._gray_pub = self.create_publisher(Image, 'rdd/gray', 10)
        self._blur_pub = self.create_publisher(Image, 'rdd/blur', 10)
        self._binary_pub = self.create_publisher(Image, 'rdd/binary', 10)
        self._processed_pub = self.create_publisher(Image, 'rdd/processed', 10)
        self._debug_pub = self.create_publisher(Image, 'rdd/debug', 10)
        self._debug_cnn_pub = self.create_publisher(Image, 'rdd/debug_cnn', 10)
        self._damage_score_pub = self.create_publisher(Float64, 'rdd/damage_score', 10)

    def preprocess_image(self, gray: np.ndarray) -> np.ndarray:
        """Enhanced image preprocessing"""
        # CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        equalized = clahe.apply(gray)
        
        # Bilateral filtering
        blurred = cv2.bilateralFilter(equalized, d=9, sigmaColor=75, sigmaSpace=75)
        
        # Multi-scale thresholding
        thresh1 = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        thresh2 = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 21, 3
        )
        
        # Combine thresholds
        binary = cv2.bitwise_and(thresh1, thresh2)
        
        # Enhanced morphological operations
        kernel_small = np.ones((3,3), np.uint8)
        kernel_large = np.ones((5,5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_small)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_large)
        
        return binary

    def analyze_features(self, contour: np.ndarray, gray_roi: np.ndarray) -> Dict:
        """Enhanced feature analysis"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # Shape features
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # Ellipse features
        if len(contour) >= 5:
            (_, _), (MA, ma), angle = cv2.fitEllipse(contour)
            eccentricity = np.sqrt(1 - (ma/MA)**2) if MA > 0 else 0
        else:
            eccentricity = 0
        
        # Contour complexity
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        complexity = len(approx)
        
        # Texture features
        glcm = graycomatrix(gray_roi, [1], [0], 256, symmetric=True, normed=True)
        contrast = graycoprops(glcm, 'contrast')[0, 0]
        homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        
        return {
            'area': area,
            'circularity': circularity,
            'solidity': solidity,
            'eccentricity': eccentricity,
            'complexity': complexity,
            'contrast': contrast,
            'homogeneity': homogeneity
        }

    def calculate_confidence(self, features: Dict) -> float:
        """Calculate confidence score from features"""
        shape_score = (
            features['circularity'] * 0.4 +
            features['solidity'] * 0.3 +
            (1 - features['eccentricity']) * 0.3
        )
        
        texture_score = (
            features['contrast'] * 0.4 +
            features['homogeneity'] * 0.6
        )
        
        # Get weights from parameters
        shape_weight = self.get_parameter('shape_weight').value
        texture_weight = self.get_parameter('texture_weight').value
        
        return shape_score * shape_weight + texture_score * texture_weight

    def predict_pothole_cnn(self, frame: np.ndarray) -> Tuple[int, float]:
        """Enhanced CNN prediction"""
        try:
            # Preprocess
            frame = cv2.resize(frame, (self.size, self.size))
            frame = frame.reshape(1, self.size, self.size, 1).astype('float32')
            frame = (frame - frame.mean()) / (frame.std() + 1e-7)
            
            # Predict
            prob = self.model.predict_proba(frame)
            max_prob = max(prob[0])
            
            # Temporal smoothing
            self.prediction_history.append(max_prob)
            if len(self.prediction_history) > self.get_parameter('temporal_window_size').value:
                self.prediction_history.pop(0)
            
            avg_confidence = sum(self.prediction_history) / len(self.prediction_history)
            
            if avg_confidence > 0.90:
                return 1, avg_confidence
            return 0, avg_confidence
            
        except Exception as e:
            self.get_logger().error(f'CNN prediction error: {str(e)}')
            return 0, 0.0

    def detect_damage(self, image: np.ndarray, img_msg: Image) -> Tuple[np.ndarray, np.ndarray, float]:
        """Enhanced damage detection pipeline with yellow box visualization"""
        try:
            # Get ROI
            height, width = image.shape[:2]
            roi_x1 = int(width * self.get_parameter('roi_x1').value)
            roi_y1 = int(height * self.get_parameter('roi_y1').value)
            roi_x2 = int(width * self.get_parameter('roi_x2').value)
            roi_y2 = int(height * self.get_parameter('roi_y2').value)
            
            # Extract ROI
            roi = image[roi_y1:roi_y2, roi_x1:roi_x2]
            debug_image = roi.copy()
            debug_cnn = roi.copy()
            
            # Publish ROI
            self._roi_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(roi, encoding='bgr8')
            )
            
            # Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            self._gray_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(gray, encoding='mono8')
            )
            
            # Enhanced preprocessing
            # 1. CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            equalized = clahe.apply(gray)
            
            # 2. Bilateral filtering for edge preservation
            blurred = cv2.bilateralFilter(equalized, d=9, sigmaColor=75, sigmaSpace=75)
            self._blur_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(blurred, encoding='mono8')
            )
            
            # 3. Multi-scale thresholding
            thresh1 = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            thresh2 = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 21, 3
            )
            binary = cv2.bitwise_and(thresh1, thresh2)
            
            # 4. Enhanced morphological operations
            kernel_small = np.ones((3,3), np.uint8)
            kernel_large = np.ones((5,5), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_small)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_large)
            
            self._binary_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(binary, encoding='mono8')
            )
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            pothole_detections = []
            
            # Process each contour
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area <= area <= self.max_area:
                    # Calculate shape features
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                    
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    solidity = float(area) / hull_area if hull_area > 0 else 0
                    
                    # Get contour ROI for texture analysis
                    contour_roi = gray[y:y+h, x:x+w]
                    if contour_roi.size > 0:
                        glcm = graycomatrix(contour_roi, [1], [0], 256, symmetric=True, normed=True)
                        contrast = graycoprops(glcm, 'contrast')[0, 0]
                        homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
                        
                        # Get thresholds from parameters
                        min_circularity = self.get_parameter('min_circularity').value
                        min_solidity = self.get_parameter('min_solidity').value
                        min_contrast = self.get_parameter('min_contrast').value
                        max_aspect_ratio = self.get_parameter('max_aspect_ratio').value
                        min_aspect_ratio = self.get_parameter('min_aspect_ratio').value
                        
                        if (circularity > min_circularity and
                            solidity > min_solidity and
                            min_aspect_ratio < aspect_ratio < max_aspect_ratio and
                            contrast > min_contrast):
                            
                            confidence = min((circularity + solidity + contrast) / 3, 1.0)
                            pothole_detections.append({
                                'contour': contour,
                                'bbox': (x, y, w, h),
                                'confidence': confidence,
                                'area': area
                            })
                            
                            # Draw yellow box for OpenCV detection
                            cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 255), 2)
                            cv2.putText(debug_image, f'Pothole {confidence:.2f}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                            cv2.drawContours(debug_image, [contour], -1, (0, 255, 255), 1)
            
            # CNN prediction
            prediction, probability = self.predict_pothole_cnn(gray)
            if prediction == 1:
                h, w = debug_cnn.shape[:2]
                # Draw green box for CNN detection
                cv2.rectangle(debug_cnn, (0, 0), (w, h), (0, 255, 0), 2)
                cv2.putText(debug_cnn, f'CNN {probability*100:.2f}%', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Convert binary to BGR for visualization
            processed_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            
            # Publish all images
            self._processed_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(processed_bgr, encoding=img_msg.encoding)
            )
            self._debug_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(debug_image, encoding=img_msg.encoding)
            )
            self._debug_cnn_pub.publish(
                self.cv_bridge.cv2_to_imgmsg(debug_cnn, encoding=img_msg.encoding)
            )
            
            return binary, debug_image, float(len(pothole_detections))
            
        except Exception as e:
            self.get_logger().error(f'Error in detect_damage: {str(e)}')
            import traceback
            self.get_logger().error(traceback.format_exc())
            return np.zeros_like(roi), roi.copy(), 0.0

    def image_callback(self, msg: Image) -> None:
        """Process incoming images"""
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg)
            resized_image = cv2.resize(cv_image, (960, 540))
            
            processed, debug_image, damage_score = self.detect_damage(resized_image, msg)
            
            score_msg = Float64()
            score_msg.data = float(damage_score)
            self._damage_score_pub.publish(score_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error in image_callback: {str(e)}')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Configuring...")
        
        # Get parameters
        self.blur_kernel = self.get_parameter('blur_kernel').value
        self.canny_low = self.get_parameter('canny_low').value
        self.canny_high = self.get_parameter('canny_high').value
        self.roi_top_ratio = self.get_parameter('roi_top_ratio').value
        self.min_area = self.get_parameter('min_area').value
        self.max_area = self.get_parameter('max_area').value
        
        # QoS Profile
        self.image_qos_profile = QoSProfile(
            reliability=self.get_parameter('image_reliability')
            .get_parameter_value()
            .integer_value,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )
        
        # Initialize publishers here instead of __init__
        self._init_publishers()
        
        super().on_configure(state)
        self.get_logger().info(f"[{self.get_name()}] Configured")
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Activating...")
        
        # Set up subscriber with correct topic name
        self.image_sub = message_filters.Subscriber(
            self, Image, "image", qos_profile=self.image_qos_profile
        )
        
        self._synchronizer = message_filters.ApproximateTimeSynchronizer(
            [self.image_sub], 10, 0.5
        )
        self._synchronizer.registerCallback(self.image_callback)
        
        super().on_activate(state)
        self.get_logger().info(f"[{self.get_name()}] Activated")
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Deactivating...")
        self.destroy_subscription(self.image_sub.sub)
        del self._synchronizer
        super().on_deactivate(state)
        self.get_logger().info(f"[{self.get_name()}] Deactivated")
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Cleaning up...")
        self.destroy_publisher(self._roi_pub)
        self.destroy_publisher(self._gray_pub)
        self.destroy_publisher(self._blur_pub)
        self.destroy_publisher(self._binary_pub)
        self.destroy_publisher(self._processed_pub)
        self.destroy_publisher(self._debug_pub)
        self.destroy_publisher(self._damage_score_pub)
        self.destroy_publisher(self._debug_cnn_pub)
        self.get_logger().info(f"[{self.get_name()}] Cleaned up")
        return TransitionCallbackReturn.SUCCESS

def main(args=None):
    rclpy.init(args=args)
    node = EnhancedRoadDamageDetector()
    
    # Automatically configure and activate the node
    node.trigger_configure()
    node.trigger_activate()
    
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()