import logging

from ..frontend.api import JoernQueryAPI
from ..datatypes import CallbackThread, MainThread, TranslationUnit, VarPublisher, SessPublisher
from ..graphutils import JoernCFG

logger = logging.getLogger(__name__)

class TUBuilder:
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
        self.translation_units = []

    
    def _getSourceFiles(self) -> list[str]:
        return self.api.get_files()
    

    def _getMainCFG(self, file_name: str) -> JoernCFG:
        main = self.api.get_cfg_as_dot(file_name, "main")[0]
        return JoernCFG(main)


    def _getSubscriberInfo(self, file_name: str) -> list[CallbackThread]:
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
    
    def _getPublishers(self, file_name: str) -> list[VarPublisher]:
        return [
            VarPublisher(key, value) 
            for item in self.api.get_var_publishers(file_name) 
            for key, value in item.items()
        ]
    
    def _getSessionPuts(self, file_name: str) -> list[SessPublisher]:
        return [
            SessPublisher(key, value) 
            for item in self.api.get_session_variables(file_name) 
            for key, value in item.items()
        ]

    def build(self) -> list[TranslationUnit]:
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
