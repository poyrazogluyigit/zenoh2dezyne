import logging
from frontend.api import JoernQueryAPI
from containers import *

logger = logging.getLogger(__name__)

class Builder:
    """Builds semantic units from Joern code graph analysis.
    
    Orchestrates queries to Joern to extract publisher/subscriber information
    and control flow data from C++ applications, producing Unit objects.
    """
    
    def __init__(self, joern_server: str = ""):
        """Initialize Builder with Joern API.
        
        Args:
            joern_server: URL of Joern server (e.g., "http://localhost:8080")
                         If empty, a local server will be started.
        """
        self.api = JoernQueryAPI(joern_server)
        self.data = {}

    def populatePublishers(self):
        """Query and populate publisher information into units."""
        pubs = self.api.get_publishers()
        for file in pubs:
            for fileName, keyExprs in file.items():
                if fileName not in self.data:
                    unit = Unit(fileName)
                else:
                    unit = self.data[fileName]
                unit.publishers = [Publisher(expr['keyExpr']) for expr in keyExprs]
                self.data[fileName] = unit
    
    def populateSubscribers(self):
        """Query and populate subscriber information into units."""
        subs = self.api.get_subscribers()
        for file in subs:
            for fileName, keyExprs in file.items():
                if fileName not in self.data:
                    unit = Unit(fileName)
                else:
                    unit = self.data[fileName]
                unit.subscribers = [Subscriber(expr['keyExpr'], expr['callback']) for expr in keyExprs]
                for subscriber in unit.subscribers:
                    puts = self.api.get_callback_control_flows(unit.filename, subscriber.callback)
                    subscriber.putStmts = [PutStmt(item['keyExpr'], item['controlFlow']) for item in puts]
                self.data[fileName] = unit
    
    def buildDict(self, project_name: str):
        """Build the unit dictionary by querying Joern for the given project.
        
        Args:
            project_name: Name of the project to analyze
            
        Returns:
            Dictionary mapping file names to Unit objects
        """
        logger.debug(f"Starting Joern analysis for project '{project_name}'")
        self.api.open_project(project_name)
        
        logger.debug("Retrieving publisher/subscriber information from Joern")
        self.populatePublishers()
        self.populateSubscribers()
        
        logger.debug("Joern analysis complete, returning unit data")
        return self.data
    
if __name__ == "__main__":
    builder = Builder()
    data = builder.buildDict("pgm-no-zenoh")
    print(data)