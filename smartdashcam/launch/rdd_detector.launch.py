from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Get the package share directory
    pkg_share = get_package_share_directory('smartdashcam')
    
    # Declare launch arguments
    blur_kernel_arg = DeclareLaunchArgument(
        'blur_kernel',
        default_value='5',
        description='Blur kernel size for image processing'
    )
    
    roi_top_ratio_arg = DeclareLaunchArgument(
        'roi_top_ratio',
        default_value='0.3',
        description='Top ratio for ROI extraction'
    )
    
    min_area_arg = DeclareLaunchArgument(
        'min_area',
        default_value='50',
        description='Minimum area for pothole detection'
    )
    
    max_area_arg = DeclareLaunchArgument(
        'max_area',
        default_value='40000',
        description='Maximum area for pothole detection'
    )
    
    min_confidence_arg = DeclareLaunchArgument(
        'min_confidence',
        default_value='0.2',
        description='Minimum confidence threshold'
    )
    
    canny_low_arg = DeclareLaunchArgument(
        'canny_low',
        default_value='100',
        description='Lower threshold for Canny edge detection'
    )
    
    canny_high_arg = DeclareLaunchArgument(
        'canny_high',
        default_value='150',
        description='Upper threshold for Canny edge detection'
    )

    temporal_window_size_arg = DeclareLaunchArgument(
        'temporal_window_size',
        default_value='5',
        description='Window size for temporal smoothing'
    )

    cnn_weight_arg = DeclareLaunchArgument(
        'cnn_weight',
        default_value='0.6',
        description='Weight for CNN detection'
    )

    opencv_weight_arg = DeclareLaunchArgument(
        'opencv_weight',
        default_value='0.4',
        description='Weight for OpenCV detection'
    )

    texture_weight_arg = DeclareLaunchArgument(
        'texture_weight',
        default_value='0.3',
        description='Weight for texture features'
    )

    shape_weight_arg = DeclareLaunchArgument(
        'shape_weight',
        default_value='0.7',
        description='Weight for shape features'
    )

    # --- ADD DECLARATIONS FOR NEW PARAMETERS ---
    min_circularity_arg = DeclareLaunchArgument(
        'min_circularity', default_value='0.5', description='Min circularity threshold'
    )
    min_solidity_arg = DeclareLaunchArgument(
        'min_solidity', default_value='0.6', description='Min solidity threshold'
    )
    min_contrast_arg = DeclareLaunchArgument(
        'min_contrast', default_value='0.6', description='Min texture contrast threshold'
    )
    max_aspect_ratio_arg = DeclareLaunchArgument(
        'max_aspect_ratio', default_value='1.5', description='Max aspect ratio threshold'
    )
    min_aspect_ratio_arg = DeclareLaunchArgument(
        'min_aspect_ratio', default_value='0.7', description='Min aspect ratio threshold'
    )
    # --- END OF NEW ARGUMENTS ---

    # Create the RDD detector node
    rdd_detector_node = Node(
        package='rdd_detector',
        executable='rdd_detector',
        name='rdd_detector',
        output='screen',
        parameters=[{
            'blur_kernel': LaunchConfiguration('blur_kernel'),
            'canny_low': LaunchConfiguration('canny_low'),
            'canny_high': LaunchConfiguration('canny_high'),
            'roi_top_ratio': LaunchConfiguration('roi_top_ratio'),
            'min_area': LaunchConfiguration('min_area'),
            'max_area': LaunchConfiguration('max_area'),
            'min_confidence': LaunchConfiguration('min_confidence'),
            'temporal_window_size': LaunchConfiguration('temporal_window_size'),
            'cnn_weight': LaunchConfiguration('cnn_weight'),
            'opencv_weight': LaunchConfiguration('opencv_weight'),
            'texture_weight': LaunchConfiguration('texture_weight'),
            'shape_weight': LaunchConfiguration('shape_weight'),
            'image_reliability': 2,  # QoSReliabilityPolicy.BEST_EFFORT
            'roi_x1': 0.4,
            'roi_y1': 0.6,
            'roi_x2': 0.6,
            'roi_y2': 0.9,
            'min_circularity': LaunchConfiguration('min_circularity'),
            'min_solidity': LaunchConfiguration('min_solidity'),
            'min_contrast': LaunchConfiguration('min_contrast'),
            'max_aspect_ratio': LaunchConfiguration('max_aspect_ratio'),
            'min_aspect_ratio': LaunchConfiguration('min_aspect_ratio'),
        }],
        remappings=[
            ('image', '/image'),
        ]
    )

    return LaunchDescription([
        # Launch arguments
        blur_kernel_arg,
        canny_low_arg,
        canny_high_arg,
        roi_top_ratio_arg,
        min_area_arg,
        max_area_arg,
        min_confidence_arg,
        temporal_window_size_arg,
        cnn_weight_arg,
        opencv_weight_arg,
        texture_weight_arg,
        shape_weight_arg,
        
        # --- ADD NEW ARGUMENTS TO LAUNCH DESCRIPTION ---
        min_circularity_arg,
        min_solidity_arg,
        min_contrast_arg,
        max_aspect_ratio_arg,
        min_aspect_ratio_arg,
        # --- END OF NEW ARGUMENTS ---
        
        # Nodes
        rdd_detector_node
    ])
