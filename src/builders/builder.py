import logging

from ..frontend import JoernClient, get_extractor

from .TUBuilder import TUBuilder
from .IGBuilder import IGBuilder, InterconnectionGraph

logger = logging.getLogger(__name__)

class Builder:
    """Orchestrates Joern analysis into an InterconnectionGraph.

    The middleware-specific extraction is injected via :func:`get_extractor`;
    Builder itself is framework-agnostic.
    """

    def __init__(self, client: JoernClient):
        self.client = client

    def build(self, middleware: str = "zenoh") -> InterconnectionGraph:
        """Build TranslationUnits and InterconnectionGraph without importing.

        Args:
            middleware: Which extractor to use ("zenoh", "ros1", "ros2", ...).

        Returns:
            The interconnection graph for the project.
        """
        extractor = get_extractor(middleware)
        logger.debug("Building Translation Unit structures with %s extractor", extractor.name)
        translation_units = TUBuilder(self.client, extractor).build()
        logger.debug("Building interconnection graph")
        graph = IGBuilder(translation_units).build()
        return InterconnectionGraph(graph)
