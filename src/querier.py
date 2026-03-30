import logging
from subprocess import Popen, PIPE
import requests
import time
import json
import re

logger = logging.getLogger(__name__)

class Querier:
    def __init__(self, joern_server: str = ""):
        self.proc = None
        self.joern_server = joern_server

    def sendQuery(self, query: str):
        if not self.proc:
            logger.error("Joern is not running. Call start() first.")
            exit(1)
        logger.debug(f"Sending query to Joern: {query[:100]}...")
        response = requests.post(
            f"{self.joern_server}/query-sync", 
            json={"query": query}
        )
        response.raise_for_status()
        logger.debug(f"Received response from Joern: {response.text[:100]}...")    
        return response.json().get("stdout", "")

    def toList(self, response: str):
        # Remove any ANSI escape sequences that Joern might include
        clean_resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)
        
        # Isolate the right-hand side of the evaluator output (e.g., `res1: String = ...`)
        if '=' in clean_resp:
            rhs = clean_resp.split('=', 1)[-1].strip()
        else:
            rhs = clean_resp.strip()
            
        # Strip Scala's string boundaries if the JSON was wrapped as a string
        if rhs.startswith('"""') and rhs.endswith('"""'):
            rhs = rhs[3:-3].strip()
        elif rhs.startswith('"') and rhs.endswith('"'):
            # Decode escaped characters like \n and \" if it's a standard string literal
            rhs = rhs[1:-1].encode('utf-8').decode('unicode_escape').strip()

        # Try to pinpoint strictly the boundaries of the JSON object/array
        match = re.search(r'([\[\{].*[\]\}])', rhs, re.DOTALL)
        if match:
            rhs = match.group(1)
            
        try:
            return json.loads(rhs)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {e}\nRaw String: {rhs}")
            exit(1)

    def start(self, timeout: int = 60):
        """Start the Joern Server process and wait for it to be ready."""
        logger.debug("Starting Joern server process...")
        self.proc = Popen(['joern', '--server'], 
                          stdin=PIPE, 
                          stdout=PIPE, 
                          stderr=PIPE, 
                          text=True)

        start_time = time.time()
        while True:
            # Check if process crashed/exited early
            if self.proc.poll() is not None:
                raise RuntimeError(f"Joern server process exited prematurely with code {self.proc.returncode}.")
            
            try:
                # Attempt to connect to the server
                requests.get(self.joern_server, timeout=1)
                logger.debug("Joern server successfully started and is reachable.")
                break  # Successful connection means server is up
            except requests.exceptions.RequestException:
                if time.time() - start_time > timeout:
                    raise RuntimeError("Joern server failed to start within the timeout.")
                time.sleep(1)


    def openCpg(self, cpg_path: str):
        """Load a CPG file into the Joern workspace."""
        if not self.proc:
            raise RuntimeError("Joern is not running. Call start() first.")
        
        command = f'importCpg("{cpg_path}")'
        return self.sendQuery(command)

    def openFile(self, source_dir: str, project_name: str):
        """Construct a CPG from source directory."""
        if not self.proc:
            raise RuntimeError("Joern is not running. Call start() first.")
        command = f'importCode(inputPath=\"{source_dir}\", projectName=\"{project_name}\")'
        return self.sendQuery(command)

    def openProject(self, project_name: str):
        """Load a project by name."""
        if not self.proc:
            raise RuntimeError("Joern is not running. Call start() first.")
        command = f'open("{project_name}")'
        return self.sendQuery(command)
    
    def workspace(self):
        """Load a project by name."""
        if not self.proc:
            raise RuntimeError("Joern is not running. Call start() first.")
        command = f'workspace'
        return self.sendQuery(command)

    def get_publishers(self):
        # Send a command to get the list of publishers
        command = '''cpg.call.name(\"declare_publisher\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code
        ))
        }.toJson'''
        return self.toList(self.sendQuery(command))

    def get_subscribers(self):
        # Send a command to get the list of subscribers
        command = '''cpg.call.name(\"declare_subscriber\").l
        .groupBy(_.file.name.headOption.getOrElse(\"unknown\"))
        .map { case (fileName, calls) =>
        fileName -> calls.map(c => Map(
        "keyExpr" -> c.argument(1).code,
        "callback" -> c.argument(2).code
        ))
        }.toJson'''
        return self.toList(self.sendQuery(command))
    
    '''
    FIXME This may not consider session.put() messages correctly
    '''
    def get_callback_control_flows(self, file_name:str, callback_name: str):
        command = f'''cpg.method("{callback_name}").call.name("put").map {{ v =>
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
      }}.toJson
        '''
        return self.toList(self.sendQuery(command))
    
    def stop(self):
        """Terminate the Joern process."""
        if self.proc:
            logger.debug("Terminating Joern process.")
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait()
            self.proc = None


if __name__ == "__main__":
    querier = Querier()
    querier.start()
    querier.openProject("pgm-no-zenoh")
    resp = querier.get_publishers()
    resp2 = querier.get_subscribers()
    resp3 = querier.get_callback_control_flows("receiver.cpp", "data_cb")
    print(resp)
    print(resp2)
    print(resp3)
    querier.stop()