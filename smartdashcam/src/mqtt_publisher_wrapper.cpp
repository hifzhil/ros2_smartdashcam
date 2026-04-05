#include <smartdashcam/mqtt_publisher_wrapper.hpp>

MqttPublisher::MqttPublisher() : Node("mqtt_publisher")
{
    vision_publisher_ = this->create_publisher<std_msgs::msg::String>("/smartdashcam/vision", 10);
    anomaly_publisher_ = this->create_publisher<std_msgs::msg::String>("/smartdashcam/anomaly", 10);
    gps_publisher_ = this->create_publisher<std_msgs::msg::String>("/smartdashcam/gps", 10);
    heartbeat_publisher_ = this->create_publisher<std_msgs::msg::String>("/smartdashcam/heartbeat", 10);
    std::this_thread::sleep_for(std::chrono::microseconds(3000));
}

void MqttPublisher::update()
{
    std_msgs::msg::String vision_data;
    std_msgs::msg::String gps_data;
    vision_data.data = vision_data_;
    gps_data.data = gps_data_;
    vision_publisher_->publish(vision_data);
    gps_publisher_->publish(gps_data);
    // RCLCPP_INFO(this->get_logger(), "Published message: %s", message.c_str());
}

void MqttPublisher::publishVisionData()
{
    std_msgs::msg::String vision_data;
    vision_data.data = vision_data_;
    vision_publisher_->publish(vision_data);
}

void MqttPublisher::publishGPSData()
{
    std_msgs::msg::String gps_data;
    gps_data.data = gps_data_;
    gps_publisher_->publish(gps_data);
}

void MqttPublisher::publishHeartbeat()
{
    std_msgs::msg::String heartbeat_data;
    heartbeat_data.data = heartbeat_data_;
    heartbeat_publisher_->publish(heartbeat_data);
}
