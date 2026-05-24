"""Private internal module for Joern server connection management.

This module is not part of the public API. Use frontend._lifecycle.JoernConnection instead.
"""
import logging
from subprocess import Popen, PIPE
import requests
import time
import atexit

logger = logging.getLogger(__name__)


class Connection:
    """Low-level Joern HTTP connection manager.
    
    This class is private and subject to change. Use JoernConnection from _lifecycle instead.
    """
    def __init__(self, joern_server: str = ""):
        self.proc = None
        self.joern_server = joern_server
        self.session = requests.Session()
        atexit.register(self._stop)
        self._start()

    def sendQuery(self, query: str):
        logger.debug(f"Sending query to Joern: {query[:100]}...")
        response = self.session.post(
            f"{self.joern_server}/query-sync", 
            json={"query": query}
        )
        response.raise_for_status()
        logger.debug(f"Received response from Joern: {response.text[:100]}...")   
        return response.json().get("stdout", "")

    def _start(self, timeout: int = 60):
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
                self.session.get(self.joern_server, timeout=1)
                logger.debug("Joern server successfully started and is reachable.")
                break  # Successful connection means server is up
            except requests.exceptions.RequestException:
                if time.time() - start_time > timeout:
                    raise RuntimeError("Joern server failed to start within the timeout.")
                time.sleep(1)

    def _stop(self):
        """Terminate the Joern process."""
        if self.proc:
            logger.debug("Terminating Joern process.")
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait()
            self.session.close()
            self.proc = None
