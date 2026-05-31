import logging

from ..frontend.api import JoernQueryAPI
from ..datatypes import CallbackThread, MainThread, TranslationUnit, VarPublisher, SessPublisher
from ..graphutils import JoernCFG

from .TUBuilder import TUBuilder
from .IGBuilder import IGBuilder, InterconnectionGraph

logger = logging.getLogger(__name__)

class Builder:
    """Builds semantic units from Joern code graph analysis.
    
    Orchestrates queries to Joern to extract publisher/subscriber information
    and control flow data from C++ applications, producing Unit objects.
    """
    
    def __init__(self, joern_api: JoernQueryAPI):
        """Initialize Builder with Joern API.
        
        Args:
            joern_server: URL of Joern server (e.g., "http://localhost:8080")
                         If empty, a local server will be started.
        """
        self.api = joern_api


    def buildProject(self, project_name: str, input_dir: str | None = None) -> InterconnectionGraph:
        """Build the interconnection graph for the given project.

        If ``input_dir`` is supplied, the source tree at that path is imported
        into the Joern workspace as ``project_name`` (which also opens it).
        Otherwise the project is assumed to already exist in the workspace
        and is just opened.

        Args:
            project_name: Joern project identifier.
            input_dir: Optional absolute path to a source directory to import.

        Returns:
            The interconnection graph for the project.
        """
        if input_dir is not None:
            logger.info(f"Creating project with {project_name}")
            print(f"creating project with {project_name}")
            self.api.import_code(input_dir, project_name)
        else:
            logger.debug(f"Opening Joern project '{project_name}'")
            self.api.open_project(project_name)

        tu_builder = TUBuilder(self.api)
        logger.debug("Building Translation Unit structures")
        translation_units = tu_builder.build()
        logger.debug("Building interconnection graph")
        graph = IGBuilder(translation_units).build()
        return InterconnectionGraph(graph)
