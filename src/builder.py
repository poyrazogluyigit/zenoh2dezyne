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
        self.translation_units = []

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

    def _build_cfg(self, dot: str) -> ControlFlowGraph:
        graph, error = parse_dot_to_graph(dot)
        if error is not None:
            logger.error(error)
            exit(1)
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        return ControlFlowGraph(
            dot=dot,
            graph=graph,
            node_count=node_count,
            edge_count=edge_count,
            parse_error=error,
        )
    
    def getSourceFiles(self) -> list[str]:
        return self.api.getFiles()
    
    def getMainCFG(self, file_name: str) -> ControlFlowGraph:
        main = self.api.getCFGAsDot(file_name, "main")[0]
        logger.debug(f"Retrieved main CFG from {file_name}: {main}")
        return self._build_cfg(main)
    


    def getSubscriberInfo(self, file_name: str) -> list[CallbackNode]:
        '''Returns a list of CallbackNodes in a given file name.'''
        subscriberData = self.api.get_callback_control_flows(file_name)
        callbackNodes = []
        for data in subscriberData:
            topic, callback, dotGraph = data['topic'], data['callback'], data['dotGraph']
            callbackNodes.append(CallbackNode(
                file_name,
                callback,
                topic,
                self._build_cfg(dotGraph)
            ))
        return callbackNodes
    

    
    '''
    0. Projedeki butun isimli dosyalari bul
    Her dosya icin:
        1. O dosyadaki subscriberlari bul
        2. Bu subscriberlarin callback fonksiyonlarinin CFGlerini ve keyexprlarini dondur
            1 ve 2 tek bir query olarak donuyor
        3. Bu dosyanin main CFGsini dondur
        4. Bu dosyadaki publishable'lari bul
            declare_publisher degiskenleri ve session degiskeni/degiskenleri
        5. Her CFG'yi publishablelara gore prunela
            control flow nodelari kalacak
            put nodelari kalacak
            bir tam ifadenin subnodelari gidecek
        6. Son CFG'leri TranslationUnit icerisinde bir araya getir
    '''
    def buildTranslationUnitStructs(self):
        self.translation_units = []
        for filename in self.getSourceFiles():
            subs = self.getSubscriberInfo(filename)
            mainCFG = self.getMainCFG(filename)
            self.translation_units.append(
                TranslationUnit(
                    main_cfg=mainCFG,
                    callback_cfgs=subs, 
                    called_method_fullnames=None
                ))

    def buildDict(self, project_name: str):
        """Build the unit dictionary by querying Joern for the given project.
        
        Args:
            project_name: Name of the project to analyze
            
        Returns:
            Dictionary mapping file names to Unit objects
        """
        logger.debug(f"Starting Joern analysis for project '{project_name}'")
        self.api.open_project(project_name)
        # self.api.import_code(input_path=project_name, project_name="basic-example-2")
        
        logger.debug("Retrieving publisher/subscriber information from Joern")
        self.populatePublishers()
        self.populateSubscribers()
        self.buildTranslationUnitStructs()
        
        logger.debug("Joern analysis complete, returning unit data")
        print(self.translation_units)
        return self.data
    
if __name__ == "__main__":
    builder = Builder()
    data = builder.buildDict("pgm-no-zenoh")
    print(data)