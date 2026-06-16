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

    def buildProject(
        self,
        project_name: str,
        input_dir: str | None = None,
        middleware: str = "zenoh",
    ) -> InterconnectionGraph:
        """Build the interconnection graph for the given project.

        If ``input_dir`` is supplied, the source tree at that path is imported
        into the Joern workspace as ``project_name`` (which also opens it).
        Otherwise the project is assumed to already exist and is just opened.

        Args:
            project_name: Joern project identifier.
            input_dir: Optional absolute path to a source directory to import.
            middleware: Which extractor to use ("zenoh", "ros1", "ros2", ...).

        Returns:
            The interconnection graph for the project.
        """
        if input_dir is not None:
            logger.info(f"Creating project with {project_name}")
            print(f"creating project with {project_name}")
            self.client.import_code(input_dir, project_name)
        else:
            logger.debug(f"Opening Joern project '{project_name}'")
            self.client.open_project(project_name)

        return self.build(middleware)
