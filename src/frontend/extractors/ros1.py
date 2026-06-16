"""ROS1 (roscpp) middleware extractor."""
from ...datatypes import Publisher, Subscriber, ServiceEndpoint
from .base import BaseExtractor
from ._ros_common import (
    extract_handle_publishers,
    extract_callback_subscribers,
    extract_service_endpoints,
)


class Ros1Extractor(BaseExtractor):
    name = "ros1"
    publish_call_names = frozenset({"publish"})

    def extract_publishers(self, client, file: str) -> list[Publisher]:
        # `advertise[<(]` matches advertise<T>(...) / advertise(...) but not
        # advertiseService(...), whose handles are services, not publishers.
        return extract_handle_publishers(client, file, "advertise[<(]")

    def extract_subscribers(self, client, file: str) -> list[Subscriber]:
        return extract_callback_subscribers(client, file, "subscribe")

    def extract_services(self, client, file: str) -> list[ServiceEndpoint]:
        return (
            extract_service_endpoints(client, file, "advertiseService", "server")
            + extract_service_endpoints(client, file, "serviceClient", "client")
        )
