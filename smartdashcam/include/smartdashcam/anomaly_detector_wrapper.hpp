#ifndef ANOMALY_DETECTOR_WRAPPER_HPP
#define ANOMALY_DETECTOR_WRAPPER_HPP

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <yolo_msgs/msg/detection.hpp>
#include <yolo_msgs/msg/detection_array.hpp>
#include <std_msgs/msg/string.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/time_synchronizer.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <cv_bridge/cv_bridge.h>
#include <unordered_map>
#include <string>
#include <ament_index_cpp/get_package_share_directory.hpp>

class AnomalyDetector : public rclcpp::Node {
public:
    AnomalyDetector();
    void runLoop();

private:
    void detectionCallback(
        const sensor_msgs::msg::Image::SharedPtr img_msg,
        const yolo_msgs::msg::DetectionArray::SharedPtr tracking_msg
    );
    void gpsCallback(const sensor_msgs::msg::NavSatFix::SharedPtr msg);
    std::string createGpsData();
    void processAnomaly(cv::Mat& cv_image, const yolo_msgs::msg::Detection& detection);

    using SyncPolicy = message_filters::sync_policies::ApproximateTime<
        sensor_msgs::msg::Image, 
        yolo_msgs::msg::DetectionArray
    >;

    message_filters::Subscriber<sensor_msgs::msg::Image> image_sub_;
    message_filters::Subscriber<yolo_msgs::msg::DetectionArray> tracking_sub_;
    std::shared_ptr<message_filters::Synchronizer<SyncPolicy>> sync_;
    
    rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr gps_sub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr anomaly_pub_;
    
    sensor_msgs::msg::NavSatFix::SharedPtr latest_gps_;
    std::unordered_map<std::string, std::unordered_map<std::string, int>> tracked_objects_;
    std::unordered_map<std::string, std::string> tracked_history_;

    const std::unordered_map<std::string, int> classes_anomaly_ = {
        {"lubang", 3},
        {"balok_kayu", 4},
        {"besi", 5},
        {"kendaraan_gangguan", 9},
        {"orang_gila", 10},
        {"genangan", 20},
        {"pohon", 22},
        {"stickcone_roboh", 28},
        {"asongan", 29},
        {"truk_parkir", 30},
        {"pecahan_ban", 31},
        {"sampah_kardus", 32},
        {"motor", 33},
        {"naik_turun_penumpang", 34},
        {"anak-anak_main_di_row", 35},
        {"kaki_empat", 36},
        {"guardrail_miring", 38},
        {"guardrail_hilang", 40}
    };

    const std::unordered_map<std::string, std::string> anomaly_translation_ = {
        {"kendaraan_gangguan", "vehicle_interference"},
        {"motor", "motor_cycle"},
        {"orang_gila", "crazy_person"},
        {"truk_parkir", "parking_truck"},
        {"lubang", "pothole"},
        {"stickcone_roboh", "stick_cone_collapse"},
        {"anak-anak_main_di_row", "child_playing_in_row"},
        {"kaki_empat", "four_legs"},
        {"guardrail_miring", "tilted_guardrail"},
        {"genangan", "puddle"},
        {"balok_kayu", "wood_beam"},
        {"besi", "iron"},
        {"asongan", "street_vendor"},
        {"pecahan_ban", "tire_fragment"},
        {"naik_turun_penumpang", "pick_up_and_drop_off_passenger"},
        {"guardrail_hilang", "guardrail_missing"},
        {"pohon", "tree"},
        {"sampah_kardus", "cardboard_trash"}
    };
};

#endif // ANOMALY_DETECTOR_WRAPPER_HPP 