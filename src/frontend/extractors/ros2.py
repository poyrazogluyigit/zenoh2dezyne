"""ROS2 (rclcpp) middleware extractor."""
from ...datatypes import Publisher, Subscriber
from .base import BaseExtractor
from ._ros_common import extract_handle_publishers, extract_callback_subscribers


class Ros2Extractor(BaseExtractor):
    name = "ros2"
    publish_call_names = frozenset({"publish"})

    def extract_publishers(self, client, file: str) -> list[Publisher]:
        return extract_handle_publishers(client, file, "create_publisher")

    def extract_subscribers(self, client, file: str) -> list[Subscriber]:
        return extract_callback_subscribers(client, file, "create_subscription")
