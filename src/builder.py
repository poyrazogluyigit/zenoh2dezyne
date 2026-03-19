from querier import Querier

class Builder:
    def __init__(self):
        self.querier = Querier()
        self.data = {}

    def populatePublishers(self, project_name: str):
        pubs = self.querier.get_publishers()
        for file in pubs:
            for fileName, keyExprs in file.items():
                key_list = [expr['keyExpr'] for expr in keyExprs]
                if fileName not in self.data:
                    self.data[fileName] = {}
                self.data[fileName]["publishers"] = key_list
    
    def populateSubscribers(self, project_name: str):
        subs = self.querier.get_subscribers()
        for file in subs:
            for fileName, keyExprs in file.items():
                key_list = [(expr['keyExpr'], expr['callback']) for expr in keyExprs]
                if fileName not in self.data:
                    self.data[fileName] = {}
                self.data[fileName]["subscribers"] = key_list
    
    def buildDict(self, project_name: str):
        self.querier.start()
        self.querier.openProject(project_name)
        self.populatePublishers(project_name)
        self.populateSubscribers(project_name)
        self.querier.stop()
        return self.data
    
if __name__ == "__main__":
    builder = Builder()
    data_dict = builder.buildDict("pgm-no-zenoh")
    print(data_dict)