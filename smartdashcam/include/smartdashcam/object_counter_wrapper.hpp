#ifndef OBJECT_COUNTER_WRAPPER_HPP
#define OBJECT_COUNTER_WRAPPER_HPP

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float64.hpp>
#include <smartdashcam_msgs/msg/object_counts.hpp>
#include <yolo_msgs/msg/detection_array.hpp>
#include <unordered_map>
#include <string>

class ObjectCounter : public rclcpp::Node
{
public:
    ObjectCounter();
    void setUpdateCallback(void (*callback)());
    void runLoop();
    const std::unordered_map<std::string, int> &getClassCounts() const
    {
        return class_counts_update_;
    }

private:
    // rclcpp::Subscription<yolo_msgs::msg::ObjectCounts>::SharedPtr subscriber_;
    // rclcpp::Subscription<yolo_msgs::msg::ObjectCounts>::SharedPtr subscriber_;
    rclcpp::Subscription<yolo_msgs::msg::DetectionArray>::SharedPtr yolo_tracking_subscriber_;
    rclcpp::Subscription<std_msgs::msg::Float64>::SharedPtr velocity_subscriber_;
    
    // void detectionsCallback(const yolo_msgs::msg::ObjectCounts::SharedPtr msg);
    void velocityCallback(const std_msgs::msg::Float64::SharedPtr msg);
    void detectionsCallback(const yolo_msgs::msg::DetectionArray::SharedPtr msg);

    std::unordered_set<std::string> counted_ids_;      
    std::unordered_map<std::string, int> class_counts_;
    std::unordered_map<std::string, int> class_counts_update_;
    
    void (*onUpdated)();                             

    bool needs_reset_ = false;    
    bool has_reset_still_counts_ = false;  
    bool is_car_moving_ = true;    

    const std::unordered_map<std::string, int> classes_to_count_ = {
        {"baliho", 0},
        {"balok_kayu", 1},
        {"besi", 2},
        {"bullnose", 3},
        {"bus", 4},
        {"cone", 5},
        {"genangan", 6},
        {"gerbang_tol", 7},
        {"guardrail", 8},
        {"guardrail_hilang", 9},
        {"guardrail_miring", 10},
        {"jpo", 11},
        {"kaki_empat", 12},
        {"kanstin_gardu", 13},
        {"kendaraan_berhenti", 14},
        {"long_booth", 15},
        {"lubang", 16},
        {"mcb", 17},
        {"mobil", 18},
        {"motor", 19},
        {"orang_dipinggir_tol", 20},
        {"overpass", 21},
        {"pagar_lubang", 22},
        {"parapet", 23},
        {"pecahan_ban", 24},
        {"petugas", 25},
        {"pju", 26},
        {"pohon", 27},
        {"rambu_gantry", 28},
        {"rambu_petunjuk", 29},
        {"rambu_standar", 30},
        {"reflektor_guidepost", 31},
        {"sampah_kardus", 32},
        {"spanduk", 33},
        {"stickcone_roboh", 34},
        {"tanaman_pot", 35},
        {"truk", 36}
    };

    const std::unordered_map<std::string, int> moving_objects_ = {
        {"bus", 4},
        {"kaki_empat", 12},
        {"mobil", 18},
        {"motor", 19},
        {"orang_dipinggir_tol", 20},
        {"petugas", 25},
        {"truk", 36}
    };

    const std::unordered_map<std::string, int> still_objects_ = {
        {"baliho", 0},
        {"balok_kayu", 1},
        {"besi", 2},
        {"bullnose", 3},
        {"cone", 5},
        {"genangan", 6},
        {"gerbang_tol", 7},
        {"guardrail", 8},
        {"guardrail_hilang", 9},
        {"guardrail_miring", 10},
        {"jpo", 11},
        {"kanstin_gardu", 13},
        {"kendaraan_berhenti", 14},
        {"long_booth", 15},
        {"lubang", 16},
        {"mcb", 17},
        {"overpass", 21},
        {"pagar_lubang", 22},
        {"parapet", 23},
        {"pecahan_ban", 24},
        {"pju", 26},
        {"pohon", 27},
        {"rambu_gantry", 28},
        {"rambu_petunjuk", 29},
        {"rambu_standar", 30},
        {"reflektor_guidepost", 31},
        {"sampah_kardus", 32},
        {"spanduk", 33},
        {"stickcone_roboh", 34},
        {"tanaman_pot", 35}
    };
};

#endif // OBJECT_COUNTER_WRAPPER_HPP