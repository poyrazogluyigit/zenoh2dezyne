import logging
import json
import re
from functools import wraps

from connection import Connection

logger = logging.getLogger(__name__)

# Rename + type + exception
def parse_joern_json(response: str) -> object:
    clean_resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)
    rhs = clean_resp.split("=", 1)[-1].strip() if "=" in clean_resp else clean_resp.strip()

    if rhs.startswith('"""') and rhs.endswith('"""'):
        rhs = rhs[3:-3].strip()
    elif rhs.startswith('"') and rhs.endswith('"'):
        rhs = rhs[1:-1].encode("utf-8").decode("unicode_escape").strip()

    match = re.search(r'([\[\{].*[\]\}])', rhs, re.DOTALL)
    if match:
        rhs = match.group(1)

    try:
        return json.loads(rhs)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse Joern JSON: {exc}") from exc


class Frontend:
    def __init__(self, joern_server: str = ""):
        self.connection = Connection(joern_server)

    @staticmethod
    def query(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            query_res = self.connection.sendQuery(result + "")
            return query_res
        return wrapper
    
    @staticmethod
    def json_query(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            query_res = self.connection.sendQuery(result + ".toJson")
            return parse_joern_json(query_res)
        return wrapper
    
    @query
    def openCpg(self, cpg_path: str):
        """Load a CPG file into the Joern workspace."""
        return f'importCpg("{cpg_path}")'

    @query
    def openFile(self, source_dir: str, project_name: str):
        """Construct a CPG from source directory."""
        return f'importCode(inputPath=\"{source_dir}\", projectName=\"{project_name}\")'

    @query
    def openProject(self, project_name: str):
        """Load a project by name."""
        return f'open("{project_name}")'

    @query
    def workspace(self):
        """Load a project by name."""
        return f'workspace'
    
    @json_query
    def getMethodsWithPut(self):
        '''Get method definitions that include a put() call.'''
        pass
    
    @json_query
    def getLambdasWithPut(self):
        '''Get lambda definitions that include a put() call.'''
        pass

    @json_query
    def getPuttableVars(self):
        '''Fetch a list of all variables for which a .put() call is valid. Here, only
        zenoh::Session and zenoh::Publisher variables are taken into account.'''
        pass

    @json_query
    def getPublisherInfo(self):
        '''Get all publisher declarations with containing files and topics they publish to.'''
        return '''cpg.call.name(\"declare_publisher\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code
        ))
        }'''

    @json_query
    def get_subscribers(self):
        '''Get all subscriber declarations with containing files
        callbacks and topics they subscribe to.'''
        return '''cpg.call.name(\"declare_subscriber\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code,
        "callback" -> c.argument(2).code
        ))
        }'''

    '''
    FIXME This may not consider session.put() messages correctly
    '''
    @json_query
    def get_callback_control_flows(self, file_name:str, callback_name: str):
        return f'''cpg.method("{callback_name}").call.name("put").map {{ v =>
        val recvName = v.receiver.isIdentifier.name.headOption.getOrElse("")
        val fname    = "{file_name}"
        
        val keyExpr = cpg.call
            .name("declare_publisher")
            .where(_.file.nameExact(fname))
            .where(_.inAssignment.argument(1).isIdentifier.nameExact(recvName))
            .argument(1)
            .code
            .headOption
            .getOrElse("")
        
        val controlFlow =
            v.inAst.isControlStructure
            .map(cs => (cs.controlStructureType, cs.condition.code.headOption.getOrElse("")))
            .l
        
        Map(
            "keyExpr"     -> keyExpr,
            "controlFlow" -> controlFlow
        )
        }}
        '''
    
if __name__ == "__main__":
    frontend = Frontend("http://localhost:8080")
    print(frontend.workspace())
    frontend.openProject("basic-example")
    print(frontend.getPublisherInfo())