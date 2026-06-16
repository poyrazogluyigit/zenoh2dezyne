"""ROS1 (roscpp) middleware extractor."""
from ...datatypes import Publisher, Subscriber
from .base import BaseExtractor
from ._ros_common import extract_handle_publishers, extract_callback_subscribers


class Ros1Extractor(BaseExtractor):
    name = "ros1"
    publish_call_names = frozenset({"publish"})

    def extract_publishers(self, client, file: str) -> list[Publisher]:
        # `advertise[<(]` matches advertise<T>(...) / advertise(...) but not
        # advertiseService(...) (which is a service, not a publisher).
        return extract_handle_publishers(client, file, "advertise[<(]")

    def extract_subscribers(self, client, file: str) -> list[Subscriber]:
        return extract_callback_subscribers(client, file, "subscribe")
