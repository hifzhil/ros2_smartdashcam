#include <ros/ros.h>
#include <string>

// ros masage data
#include <nav_msgs/Odometry.h>

class ObjectCounter
{
public:
    ObjectCounter();

private:
    ros::NodeHandle handler;
    ros::Subscriber subscriber;
    void detectionsCallback(const yolo_msgs::msg::DetectionArray::SharedPtr msg);
};