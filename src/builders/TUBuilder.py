import logging

from ..frontend.api import JoernQueryAPI
from ..datatypes import Subscriber, MainThread, TranslationUnit, Publisher
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


    def _getSubscriberInfo(self, file_name: str) -> list[Subscriber]:
        '''Returns the subscriptions declared in a given file.'''
        subscriberData = self.api.get_callback_control_flows(file_name)
        subscribers = []
        for data in subscriberData:
            topic, callback_name, dotGraph = data['topic'], data['callback'], data['dotGraph']
            subscribers.append(Subscriber(callback_name, topic, JoernCFG(dotGraph)))
        return subscribers

    def _getPublishers(self, file_name: str) -> list[Publisher]:
        publishers = [
            Publisher(symbol=key, topic=value)
            for item in self.api.get_var_publishers(file_name)
            for key, value in item.items()
        ]
        for item in self.api.get_session_variables(file_name):
            for session_var, topics in item.items():
                publishers.extend(Publisher(symbol=session_var, topic=t) for t in topics)
        return publishers

    def build(self) -> list[TranslationUnit]:
        translation_units = []
        for filename in self._getSourceFiles():
            subs = self._getSubscriberInfo(filename)
            mainCFG = self._getMainCFG(filename)
            publishers = self._getPublishers(filename)
            translation_units.append(
                TranslationUnit(
                    file_name=filename,
                    main_thread=MainThread(cfg=mainCFG),
                    callback_threads=subs,
                    publishers=publishers,
                ))
        return translation_units
