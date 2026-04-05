cmake_minimum_required(VERSION 3.8)
project(smartdashcam)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(yolo_msgs REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(smartdashcam_msgs REQUIRED)

# Install Python module
ament_python_install_package(${PROJECT_NAME})

# Install Python scripts
install(PROGRAMS
  scripts/anomaly_detector_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME anomaly_detector
)

# install(PROGRAMS
#   scripts/dbg_yolo_node.py
#   DESTINATION lib/${PROJECT_NAME}
#   RENAME dbg_yolo
# )
# C++ setup continues...
include_directories(
  include
  ${smartdashcam_msgs_INCLUDE_DIRS}
)

add_executable(smartdashcam_main 
  src/smartdashcam_main.cpp 
  src/object_counter_wrapper.cpp
  src/mqtt_publisher_wrapper.cpp
  src/gps_wrapper.cpp
)

ament_target_dependencies(smartdashcam_main rclcpp yolo_msgs std_msgs sensor_msgs nlohmann_json yaml-cpp ament_index_cpp)

target_link_libraries(smartdashcam_main yaml-cpp)

install(TARGETS
  smartdashcam_main
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(
  FILES
  config/gscam_pipeline.yaml
  config/yolov8_config.yaml
  config/gps_config.yaml
  config/smartdashcam_config.yaml
  config/smartdashcam_config_default.yaml
  DESTINATION share/${PROJECT_NAME}/config
)

set(CRT_FILES_PATH "${CMAKE_CURRENT_SOURCE_DIR}/config/.crt")

install(FILES 
    ${CRT_FILES_PATH}/ca.crt
    ${CRT_FILES_PATH}/client.crt
    ${CRT_FILES_PATH}/client.key
    DESTINATION share/${PROJECT_NAME}/config/.crt
)

install(
    FILES
    config/sa.json
    DESTINATION share/${PROJECT_NAME}/config
)

# Model directory
install(
  FILES
  config/model/your_model.pt
  config/model/full_model.h5
  DESTINATION share/${PROJECT_NAME}/config/model
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
