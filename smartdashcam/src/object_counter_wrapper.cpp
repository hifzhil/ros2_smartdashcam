#include <smartdashcam/object_counter_wrapper.hpp>
#include <unordered_map>

ObjectCounter::ObjectCounter() : Node("object_counter"), onUpdated(nullptr)
{
    // subscriber_ = this->create_subscription<yolo_msgs::msg::ObjectCounts>(
    //     "/yolo/objects/counts", 10, 
    //     std::bind(&ObjectCounter::detectionsCallback, this, std::placeholders::_1));
    
    yolo_tracking_subscriber_ = this->create_subscription<yolo_msgs::msg::DetectionArray>(
        "/yolo/tracking", 10, std::bind(&ObjectCounter::detectionsCallback, this, std::placeholders::_1));

    velocity_subscriber_ = this->create_subscription<std_msgs::msg::Float64>(
        "/velocity",  
        10,                
        std::bind(&ObjectCounter::velocityCallback, this, std::placeholders::_1)
    );
    /**
     * @brief: Initiate the container for counted object
     *          structure : <string, int> 
     */
    for (const auto &class_pair : classes_to_count_)
    {
        class_counts_[class_pair.first] = 0;
    }
    
    for (const auto &class_pair : classes_to_count_)
    {
        class_counts_update_[class_pair.first] = 0;
    }
}

void ObjectCounter::detectionsCallback(const yolo_msgs::msg::DetectionArray::SharedPtr msg)
{

    class_counts_update_.clear();
    for (const auto &class_pair : classes_to_count_)
    {
        class_counts_update_[class_pair.first] = 0;
    }

    /**
     * @brief: State Transition Pattern for Flip-Flop   
     *          is_car_moving_ is the trigger condition
     *          needs_reset_ is the flip-flop state
     *          has_reset_still_counts_ is the action completion flag
     */
    if (!is_car_moving_ && !needs_reset_)
    {
        needs_reset_ = true;
        RCLCPP_INFO(this->get_logger(), "Car stopped - preparing to reset still object counts");
    }
    else if (is_car_moving_ && needs_reset_)
    {
        needs_reset_ = false;
        has_reset_still_counts_ = false;
        RCLCPP_INFO(this->get_logger(), "Car moving - reset flag cleared");
    }

    // Reset counts if needed before processing new detections
    if (!is_car_moving_ && needs_reset_ && !has_reset_still_counts_)
    {
        // Reset ALL counts to 0 and record the changes
        for (const auto &class_pair : classes_to_count_)
        {
            int previous_count = class_counts_[class_pair.first];
            class_counts_[class_pair.first] = 0;
            
            // Record the change in class_counts_update_
            if (previous_count > 0)
            {
                class_counts_update_[class_pair.first] = -previous_count;
            }
        }
        has_reset_still_counts_ = true;
        RCLCPP_INFO(this->get_logger(), "Reset all object counts to 0");
    }

    bool updated = false;

    for (const auto &detection : msg->detections)
    {
        if (classes_to_count_.find(detection.class_name) != classes_to_count_.end())
        {
            if (counted_ids_.find(detection.id) == counted_ids_.end())
            {
                bool is_still_object = (still_objects_.find(detection.class_name) != still_objects_.end());
                counted_ids_.insert(detection.id);
                int previous_count = class_counts_[detection.class_name];

                if (is_still_object)
                {
                    if (!is_car_moving_)
                    {
                        class_counts_[detection.class_name] = std::min(previous_count + 1, 1);
                    }
                    else
                    {
                        class_counts_[detection.class_name]++;
                    }
                }
                else
                {
                    class_counts_[detection.class_name]++;
                }

                int change = class_counts_[detection.class_name] - previous_count;
                if (change > 0)
                {
                    class_counts_update_[detection.class_name] = change;
                    updated = true;
                }

                RCLCPP_INFO(this->get_logger(), "Counted object: %s, Total Count: %d", 
                           detection.class_name.c_str(), 
                           class_counts_[detection.class_name]);
            }
        }
    }

    if (updated && onUpdated != nullptr)
    {
        onUpdated();
    }
}

void ObjectCounter::velocityCallback(const std_msgs::msg::Float64::SharedPtr msg)
{

    double velocity_threshold = 5.0; 

    if (msg->data > velocity_threshold)
    {
        is_car_moving_ = true;  // Car is moving
        has_reset_still_counts_ = false;
    }
    else
    {
        is_car_moving_ = false; // Car is not moving
    }

    // RCLCPP_INFO(this->get_logger(), "Car moving state: %s", is_car_moving_ ? "true" : "false");
}

void ObjectCounter::setUpdateCallback(void (*callback)())
{
    onUpdated = callback;
}

void ObjectCounter::runLoop()
{
    rclcpp::spin(shared_from_this());
}
