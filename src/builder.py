import logging
from frontend.api import JoernQueryAPI
from containers import *
from graphutils import parse_dot_to_graph

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
        self.callback_cfgs = []
        self.main_cfgs = []

    def _build_cfg(self, dot: str) -> ControlFlowGraph:
        graph, error = parse_dot_to_graph(dot)
        node_count = graph.number_of_nodes() if graph else 0
        edge_count = graph.number_of_edges() if graph else 0
        return ControlFlowGraph(
            dot=dot,
            graph=graph,
            node_count=node_count,
            edge_count=edge_count,
            parse_error=error,
        )

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
                self.data[fileName] = unit

    def populateCallbackCFGs(self):
        """Query and parse callback CFGs into graph objects."""
        self.callback_cfgs = []
        subscriber_index = {}
        for unit in self.data.values():
            for subscriber in unit.subscribers:
                subscriber_index[(subscriber.callback, subscriber.keyExpr)] = unit.filename

        callback_cfgs = self.api.get_callback_control_flows()
        for item in callback_cfgs:
            key_expr = item.get("topic", item.get("keyExpr", ""))
            callback = item.get("callback", "")
            dot_graph = item.get("dotGraph", "")
            file_name = subscriber_index.get((callback, key_expr), "unknown")
            cfg = self._build_cfg(dot_graph)
            self.callback_cfgs.append(
                CallbackCFG(
                    file_name=file_name,
                    callback=callback,
                    key_expr=key_expr,
                    cfg=cfg,
                )
            )

    def populateMainCFGs(self):
        """Query and parse main() CFGs into graph objects."""
        self.main_cfgs = []
        main_cfgs = self.api.get_main_control_flows()
        for item in main_cfgs:
            file_name = item.get("file", "unknown")
            dot_graph = item.get("dotCfg", "")
            cfg = self._build_cfg(dot_graph)
            self.main_cfgs.append(MainCFG(file_name=file_name, cfg=cfg))
    
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
        self.populateCallbackCFGs()
        self.populateMainCFGs()
        
        logger.debug("Joern analysis complete, returning unit data")
        return self.data
    
if __name__ == "__main__":
    builder = Builder()
    data = builder.buildDict("pgm-no-zenoh")
    print(data)