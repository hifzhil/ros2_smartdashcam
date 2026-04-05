#ifndef GPS_WRAPPER_HPP
#define GPS_WRAPPER_HPP

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <std_msgs/msg/float64.hpp>
#include <string>
#include <cmath>

class GpsWrapper : public rclcpp::Node
{
public:
    GpsWrapper();
    void setUpdateCallback(void (*callback)());
    void runLoop();
    struct GPSData
    {
        double latitude;
        double longitude;
        double altitude;
        double velocity;
    };
    GPSData getGpsData() const;
    bool isInBase() const;
    double calculateDistance(double lat1, double lon1, double lat2, double lon2) const;

    double latitude;
    double longitude;
    double altitude;
    double velocity;
    double distance;
    bool is_car_moving;
    bool first_msg;
private:
    void gpsCallback(const sensor_msgs::msg::NavSatFix::SharedPtr msg);
    
    rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr gps_subscription_;
    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr velocity_pub_;
    
    double latitude_;
    double longitude_;
    double altitude_;
    double velocity_;
    double distance_;
    bool is_car_moving_;
    
    double prev_latitude_;
    double prev_longitude_;
    rclcpp::Time prev_time_;
    bool first_msg_;
    
    const double EARTH_RADIUS = 6371000.0;
    void (*onUpdated)();
    
    const double BASE_LAT = -6.220533666666666;
    const double BASE_LON = 106.63464175;
    const double BASE_RADIUS = 50.0;

};

#endif // GPS_WRAPPER_HPP