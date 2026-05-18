import logging
from frontend.querier import Querier
from containers import *

logger = logging.getLogger(__name__)

class Builder:
    def __init__(self, joern_server: str = ""):
        self.querier = Querier(joern_server)
        self.data = {}

    def populatePublishers(self):
        pubs = self.querier.get_publishers()
        for file in pubs:
            for fileName, keyExprs in file.items():
                if fileName not in self.data:
                    unit = Unit(fileName)
                else:
                    unit = self.data[fileName]
                unit.publishers = [Publisher(expr['keyExpr']) for expr in keyExprs]
                self.data[fileName] = unit
    
    def populateSubscribers(self):
        subs = self.querier.get_subscribers()
        for file in subs:
            for fileName, keyExprs in file.items():
                if fileName not in self.data:
                    unit = Unit(fileName)
                else:
                    unit = self.data[fileName]
                unit.subscribers = [Subscriber(expr['keyExpr'], expr['callback']) for expr in keyExprs]
                for subscriber in unit.subscribers:
                    puts = self.querier.get_callback_control_flows(unit.filename, subscriber.callback)
                    subscriber.putStmts = [PutStmt(item['keyExpr'], item['controlFlow']) for item in puts]
                self.data[fileName] = unit
    
    def buildDict(self, project_name: str):
        logger.debug(f"Starting Joern Querier to process project '{project_name}'")
        self.querier.start()
        self.querier.openProject(project_name)
        
        logger.debug("Retrieving publisher/subscriber information from Joern")
        self.populatePublishers()
        self.populateSubscribers()
        
        # logger.debug("Stopping Joern Querier and returning unit data")
        # self.querier.stop()
        return self.data
    
if __name__ == "__main__":
    builder = Builder()
    data = builder.buildDict("pgm-no-zenoh")
    print(data)