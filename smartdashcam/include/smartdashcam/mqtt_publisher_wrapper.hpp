#ifndef MQTT_PUBLISHER_WRAPPER_HPP
#define MQTT_PUBLISHER_WRAPPER_HPP

#include <rclcpp/rclcpp.hpp>
#include <string>
#include <std_msgs/msg/string.hpp>

class MqttPublisher : public rclcpp::Node
{
public:
    MqttPublisher();
    void update();
    std::string vision_data_;
    std::string anomaly_data_;
    std::string gps_data_;
    std::string heartbeat_data_;
    void publishVisionData();
    void publishGPSData();
    void publishHeartbeat();
private:
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr vision_publisher_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr anomaly_publisher_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr gps_publisher_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr heartbeat_publisher_;
};

#endif // MQTT_PUBLISHER_WRAPPER_HPP