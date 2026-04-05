#include <smartdashcam/gps_wrapper.hpp>

GpsWrapper::GpsWrapper() 
    : Node("gps_wrapper"), 
      latitude_(0.0), longitude_(0.0), altitude_(0.0), velocity_(0.0), distance_(0.0),
      first_msg_(true), onUpdated(nullptr)
{
    // Subscribe to /fix topic
    gps_subscription_ = this->create_subscription<sensor_msgs::msg::NavSatFix>(
        "/fix", 10, std::bind(&GpsWrapper::gpsCallback, this, std::placeholders::_1));
        
    // Create velocity publisher
    velocity_pub_ = this->create_publisher<std_msgs::msg::Float64>("/velocity", 10);
}

double GpsWrapper::calculateDistance(double lat1, double lon1, double lat2, double lon2) const
{
    double lat1_rad = lat1 * M_PI / 180.0;
    double lon1_rad = lon1 * M_PI / 180.0;
    double lat2_rad = lat2 * M_PI / 180.0;
    double lon2_rad = lon2 * M_PI / 180.0;

    double dlat = lat2_rad - lat1_rad;
    double dlon = lon2_rad - lon1_rad;
    double a = std::sin(dlat/2) * std::sin(dlat/2) +
               std::cos(lat1_rad) * std::cos(lat2_rad) *
               std::sin(dlon/2) * std::sin(dlon/2);
    double c = 2 * std::atan2(std::sqrt(a), std::sqrt(1-a));
    
    return EARTH_RADIUS * c;
}

void GpsWrapper::gpsCallback(const sensor_msgs::msg::NavSatFix::SharedPtr msg)
{
    if (std::isnan(msg->latitude) || std::isnan(msg->longitude) || std::isnan(msg->altitude))
    {
        RCLCPP_WARN(this->get_logger(), "Received NaN values in GPS data, skipping update.");
        return;
    }

    rclcpp::Time current_time = this->now();

    if (!first_msg_)
    {
        double dt = (current_time - prev_time_).seconds();
        if (dt > 0)
        {
            distance_ = calculateDistance(
                prev_latitude_, prev_longitude_,
                msg->latitude, msg->longitude
            );
            
            velocity_ = distance_ / dt;  // Fixed: using distance_ instead of distance
            is_car_moving_ = (velocity_ > 0.05); 
            auto velocity_msg = std_msgs::msg::Float64();
            velocity_msg.data = velocity_ * 3.6;
            velocity_pub_->publish(velocity_msg);
            
            RCLCPP_INFO(this->get_logger(), 
                       "Velocity: %.2f m/s (%.2f km/h)", 
                       velocity_, velocity_ * 3.6);
        }
    }
    else
    {
        first_msg_ = false;
    }

    // Store previous values
    prev_latitude_ = msg->latitude;
    prev_longitude_ = msg->longitude;
    prev_time_ = current_time;

    // Update current values
    latitude_ = msg->latitude;
    longitude_ = msg->longitude;
    altitude_ = msg->altitude;
    
    // Update public members
    latitude = latitude_;
    longitude = longitude_;
    altitude = altitude_;
    velocity = velocity_;
    distance = distance_;
    is_car_moving = is_car_moving_;
    first_msg = first_msg_;

    RCLCPP_INFO(this->get_logger(), "Updated GPS data: lat=%.6f, lon=%.6f, alt=%.2f, Distance: %.2f m",
                latitude_, longitude_, altitude_, distance_);

    if (onUpdated != nullptr)
    {
        onUpdated();
    }
}

GpsWrapper::GPSData GpsWrapper::getGpsData() const
{
    return {latitude_, longitude_, altitude_, velocity_};
}

void GpsWrapper::setUpdateCallback(void (*callback)())
{
    onUpdated = callback;
}

void GpsWrapper::runLoop()
{
    rclcpp::Rate rate(0.5); // 1 Hz
    while (rclcpp::ok())
    {
        rclcpp::spin_some(shared_from_this());
        rate.sleep();
    }
}

bool GpsWrapper::isInBase() const {
    if (std::isnan(latitude_) || std::isnan(longitude_)) {
        RCLCPP_WARN(this->get_logger(), "Cannot determine base location - GPS coordinates are NaN");
        return false;
    }

    double distance = calculateDistance(
        latitude_, longitude_,
        BASE_LAT, BASE_LON
    );

    bool is_in_base = distance <= BASE_RADIUS;
    
    RCLCPP_DEBUG(this->get_logger(), 
                 "Distance to base: %.2f m (In base: %s)", 
                 distance, 
                 is_in_base ? "true" : "false");

    return is_in_base;
}