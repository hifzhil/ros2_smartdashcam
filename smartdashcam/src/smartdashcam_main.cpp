#include <rclcpp/rclcpp.hpp>
#include <smartdashcam/object_counter_wrapper.hpp>
#include <smartdashcam/mqtt_publisher_wrapper.hpp>
#include <smartdashcam/gps_wrapper.hpp>
#include <nlohmann/json.hpp>
#include <memory>
#include <iostream>
#include <iomanip>
#include <chrono>
#include <ctime>
#include <sstream>
#include <mutex>
#include <rclcpp/executors/single_threaded_executor.hpp>
#include <yaml-cpp/yaml.h>
#include <ament_index_cpp/get_package_share_directory.hpp>

std::shared_ptr<MqttPublisher> mqttPublisher;
std::shared_ptr<GpsWrapper> gpsWrapper;
std::shared_ptr<ObjectCounter> objectCounter;
std::mutex update_mutex;

rclcpp::Time last_check_time_;
std::string last_camera_status_ = "inactive";
std::string last_gps_status_ = "inactive";
const int HEARTBEAT_INTERVAL_SEC = 30;

std::unordered_map<std::string, std::string> loadConfigurations()
{
    std::unordered_map<std::string, std::string> config_map;
    std::string config_file_path =
        ament_index_cpp::get_package_share_directory("smartdashcam") + "/config/smartdashcam_config.yaml";

    /**
     * @brief Load the YAML configuration file
     */
    YAML::Node config;
    try {
        config = YAML::LoadFile(config_file_path);
    } catch (const std::exception &e) {
        RCLCPP_ERROR(rclcpp::get_logger("loadConfigurations"), "Failed to load config: %s", e.what());
    }

    config_map["dashcam_id"] = config["device"]["ros__parameters"]["dashcam_id"].as<std::string>();
    config_map["device_id"] = config["device"]["ros__parameters"]["device_id"].as<std::string>();
    config_map["ruas_id"] = config["device"]["ros__parameters"]["ruas_id"].as<std::string>();
    config_map["timezone"] = config["device"]["ros__parameters"]["timezone"].as<std::string>();

    return config_map;
}

std::string format_rfc3339(const std::chrono::system_clock::time_point &tp)
{
    using namespace std::chrono;
    std::time_t time = system_clock::to_time_t(tp);
    std::tm tm = *std::gmtime(&time);
    std::stringstream ss;
    ss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S");
    auto microseconds = duration_cast<std::chrono::microseconds>(tp.time_since_epoch()) % 1000000;
    ss << "." << std::setw(6) << std::setfill('0') << microseconds.count();
    ss << "+00:00";
    return ss.str();
}

std::string createJsonStringVision(const std::unordered_map<std::string, int> &class_counts, const std::unordered_map<std::string, std::string> &config)
{
    using namespace std::chrono;

    nlohmann::json json_data;
    for (const auto &pair : class_counts)
    {
        json_data[pair.first] = pair.second;
    }
    auto now = system_clock::now();
    json_data["dashcam_id"] = config.at("dashcam_id");
    json_data["device_id"] = config.at("device_id");
    json_data["ruas_id"] = config.at("ruas_id");
    json_data["start_time"] = format_rfc3339(now);
    json_data["end_time"] = format_rfc3339(now + seconds(1));
    json_data["timezone"] = config.at("timezone");
    json_data["type"] = "counting";

    return json_data.dump();
}

/**
 * @Flag; Multiple copy of a class?
 */

/**
 * @TODO: Change this method
 */
std::string createJsonStringGPS(double latitude, double longitude, double altitude, 
                                 double velocity, double total_distance, 
                                 bool is_car_moving, 
                                 const std::unordered_map<std::string, std::string> &config)
{
    using namespace std::chrono;
    auto now = system_clock::now();

    nlohmann::json json_data = {
        {"device_id", config.at("device_id")},
        {"dashcam_id", config.at("dashcam_id")},
        {"ruas_id", config.at("ruas_id")},
        {"timezone", config.at("timezone")},
        {"date_time", format_rfc3339(now)},
        {"latitude", latitude},
        {"longitude", longitude},
        {"altitude", altitude},
        {"velocity", velocity},
        {"total_distance", total_distance},
        {"true_north_heading", " degree"},
        {"magnetic_north_heading", " degree"},
        {"ground_speed", "0 Kn"},
        {"ground_speed_km", "0 Km/h"}
    };

    return json_data.dump();
}

std::string checkGpsPort() {
    std::string cmd = "stat /dev/ttyUSB1 2>&1";
    char buffer[256];
    std::string stat_output;
    
    FILE* pipe = popen(cmd.c_str(), "r");
    if (pipe) {
        while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
            stat_output += buffer;
        }
        pclose(pipe);

        if (stat_output.find("character special file") != std::string::npos) {
            if (gpsWrapper->first_msg) {
                last_gps_status_ = "error";
            } else if (std::isnan(gpsWrapper->latitude) || std::isnan(gpsWrapper->longitude)) {
                last_gps_status_ = "nofix";
            } else {
                last_gps_status_ = "active";
            }
        } else {
            last_gps_status_ = "inactive";
            RCLCPP_ERROR(rclcpp::get_logger("heartbeat"), "GPS inactive: Port not found");
        }
    }
    return last_gps_status_;
}

std::string checkCameraStatus() {
    std::string cmd = "ping -c 1 -W 1 192.168.0.1 2>&1";
    char buffer[128];
    std::string ping_output;
    
    FILE* pipe = popen(cmd.c_str(), "r");
    if (pipe) {
        while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
            ping_output += buffer;
        }
        pclose(pipe);

        if (ping_output.find("100% packet loss") != std::string::npos) {
            last_camera_status_ = "inactive";
            RCLCPP_ERROR(rclcpp::get_logger("heartbeat"), "Camera inactive: Network unreachable");
        } else if (ping_output.find("bytes from 192.168.0.1") != std::string::npos) {
            last_camera_status_ = "active";
        } else {
            last_camera_status_ = "error";
        }
    }
    return last_camera_status_;
}

std::string createJsonStringHeartbeat(const std::unordered_map<std::string, std::string>& config) {
    using namespace std::chrono;
    auto now = system_clock::now();

    nlohmann::json json_data = {
        {"device_id", config.at("device_id")},
        {"dashcam_id", config.at("dashcam_id")},
        {"ruas_id", config.at("ruas_id")},
        {"timezone", config.at("timezone")},
        {"date_time", format_rfc3339(now)},
        {"status", "online"},
        {"gps", last_gps_status_},
        {"camera", last_camera_status_},
        {"is_car_moving", gpsWrapper->is_car_moving},
        {"is_on_base", gpsWrapper->isInBase()}
    };

    return json_data.dump();
}

void updateHeartbeat() {
    std::lock_guard<std::mutex> lock(update_mutex);
    RCLCPP_INFO(rclcpp::get_logger("updateHeartbeat"), "Updating heartbeat data");

    try {
        checkGpsPort();
        checkCameraStatus();

        if (mqttPublisher) {
            std::string json_string_heartbeat = createJsonStringHeartbeat(loadConfigurations());
            RCLCPP_INFO(rclcpp::get_logger("updateHeartbeat"), 
                       "Heartbeat data: GPS=%s, Camera=%s", 
                       last_gps_status_.c_str(), 
                       last_camera_status_.c_str());
            
            mqttPublisher->heartbeat_data_ = json_string_heartbeat;
            mqttPublisher->publishHeartbeat();
        }
    } catch (const std::exception& e) {
        RCLCPP_ERROR(rclcpp::get_logger("updateHeartbeat"), "Error updating heartbeat: %s", e.what());
    }
}

void updateVision()
{
    std::lock_guard<std::mutex> lock(update_mutex);
    RCLCPP_INFO(rclcpp::get_logger("updateVision"), "Updating vision data");

    std::string json_string_vision = createJsonStringVision(objectCounter->getClassCounts(), loadConfigurations());
    mqttPublisher->vision_data_ = json_string_vision;
    mqttPublisher->publishVisionData();
}

void updateGPS()
{
    std::lock_guard<std::mutex> lock(update_mutex);
    RCLCPP_INFO(rclcpp::get_logger("updateGPS"), "Updating GPS data: lat=%.6f, lon=%.6f, alt=%.2f",
                gpsWrapper->latitude, gpsWrapper->longitude, gpsWrapper->altitude);

    std::string json_string_gps = createJsonStringGPS(gpsWrapper->latitude, gpsWrapper->longitude, gpsWrapper->altitude, gpsWrapper->velocity, gpsWrapper->distance, gpsWrapper->is_car_moving, loadConfigurations());
    mqttPublisher->gps_data_ = json_string_gps;
    mqttPublisher->publishGPSData();
}

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    // Create nodes
    mqttPublisher = std::make_shared<MqttPublisher>();
    gpsWrapper = std::make_shared<GpsWrapper>();
    objectCounter = std::make_shared<ObjectCounter>();

    objectCounter->setUpdateCallback(&updateVision); 

    gpsWrapper->setUpdateCallback(&updateGPS);
    // Heartbeat timer
    auto heartbeat_timer = mqttPublisher->create_wall_timer(
        std::chrono::seconds(HEARTBEAT_INTERVAL_SEC),
        []() {
            updateHeartbeat();
        }
    );

    // Create executor and add nodes
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(mqttPublisher);
    executor.add_node(gpsWrapper);
    executor.add_node(objectCounter);

    // Spin the executor
    executor.spin();

    rclcpp::shutdown();
    return 0;
}
