import logging

from ..frontend.api import JoernQueryAPI
from ..datatypes import CallbackThread, MainThread, TranslationUnit, VarPublisher, SessPublisher
from ..graphutils import JoernCFG

from .TUBuilder import TUBuilder
from .IGBuilder import IGBuilder

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


    def buildProject(self, project_name: str) -> list[TranslationUnit]:
        """Build the unit dictionary by querying Joern for the given project.
        
        Args:
            project_name: Name of the project to analyze
            
        Returns:
            Dictionary mapping file names to Unit objects
        """
        logger.debug(f"Starting Joern analysis for project '{project_name}'")
        self.api.open_project(project_name)        
        tu_builder = TUBuilder(self.api)
        logger.debug("Building Translation Unit structures")
        translation_units = tu_builder.build()
        logger.debug("Building interconnection graph")
        graph = IGBuilder(translation_units).build()
        return graph
