#include <chrono>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

int main(int argc, char ** argv) {
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("talker");

    auto chatter_pub = node->create_publisher<std_msgs::msg::String>("chatter", 10);

    while (rclcpp::ok()) {
        auto msg = std_msgs::msg::String();
        msg.data = "hello";
        chatter_pub->publish(msg);
    }

    rclcpp::shutdown();
    return 0;
}
