import logging
from frontend.api import JoernQueryAPI
from datatypes._datatypes import CallbackThread, MainThread, TranslationUnit, VarPublisher, SessPublisher
from graphutils import JoernCFG

logger = logging.getLogger(__name__)

class Builder:
    """Builds semantic units from Joern code graph analysis.
    
    Orchestrates queries to Joern to extract publisher/subscriber information
    and control flow data from C++ applications, producing Unit objects.
    """
    
    def __init__(self, joern_server: str = "", api=None):
        """Initialize Builder with Joern API.
        
        Args:
            joern_server: URL of Joern server (e.g., "http://localhost:8080")
                         If empty, a local server will be started.
        """
        self.api = api
        self.translation_units = []

    
    def getSourceFiles(self) -> list[str]:
        return self.api.get_files()
    

    def getMainCFG(self, file_name: str) -> JoernCFG:
        main = self.api.get_cfg_as_dot(file_name, "main")[0]
        return JoernCFG(main)


    def getSubscriberInfo(self, file_name: str) -> list[CallbackThread]:
        '''Returns a list of CallbackNodes in a given file name.'''
        subscriberData = self.api.get_callback_control_flows(file_name)
        callbackNodes = []
        for data in subscriberData:
            topic, callback_name, dotGraph = data['topic'], data['callback'], data['dotGraph']
            callbackNodes.append(CallbackThread(
                callback_name,
                topic,
                JoernCFG(dotGraph)
            ))
        return callbackNodes
    
    def getPublishers(self, file_name: str) -> list[VarPublisher]:
        return [
            VarPublisher(key, value) 
            for item in self.api.get_var_publishers(file_name) 
            for key, value in item.items()
        ]
    
    def getSessionPuts(self, file_name: str) -> list[SessPublisher]:
        return [
            SessPublisher(key, value) 
            for item in self.api.get_session_variables(file_name) 
            for key, value in item.items()
        ]

    
    '''
    0. Projedeki butun isimli dosyalari bul
    Her dosya icin:
        1. O dosyadaki subscriberlari bul
        2. Bu subscriberlarin callback fonksiyonlarinin CFGlerini ve keyexprlarini dondur
            1 ve 2 tek bir query olarak donuyor
        3. Bu dosyanin main CFGsini dondur
        4. Bu dosyadaki publishable'lari bul
            4.1 bu dosyadaki publisher'lari (degisken, topic) olarak dondur
            4.2 bu dosyadaki session degiskenlerini (degisken, [topic list]) olarak dondur
        5. Her CFG'yi publishablelara gore prunela
            control flow nodelari kalacak
            put nodelari kalacak
            bir tam ifadenin subnodelari gidecek
        6. Son CFG'leri TranslationUnit icerisinde bir araya getir
    '''
    def buildTranslationUnitStructs(self) -> list[TranslationUnit]:
        translation_units = []
        for filename in self.getSourceFiles():
            subs = self.getSubscriberInfo(filename)
            mainCFG = self.getMainCFG(filename)
            pubVars = self.getPublishers(filename)
            sessionPubs = self.getSessionPuts(filename)
            translation_units.append(
                TranslationUnit(
                    file_name=filename,
                    main=MainThread(cfg=mainCFG),
                    callbacks=subs, 
                    var_publishers=pubVars,
                    sess_publishers=sessionPubs,
                ))
        return translation_units

    def buildProject(self, project_name: str) -> list[TranslationUnit]:
        """Build the unit dictionary by querying Joern for the given project.
        
        Args:
            project_name: Name of the project to analyze
            
        Returns:
            Dictionary mapping file names to Unit objects
        """
        logger.debug(f"Starting Joern analysis for project '{project_name}'")
        self.api.open_project(project_name)        
        logger.debug("Retrieving publisher/subscriber information from Joern")
        data = self.buildTranslationUnitStructs()
        logger.debug("Joern analysis complete, returning unit data")
        return data
