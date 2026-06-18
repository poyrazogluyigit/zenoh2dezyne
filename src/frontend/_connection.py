"""Private internal module for Joern server connection management.

This module is not part of the public API. Use frontend._lifecycle.JoernConnection instead.
"""
import logging
from subprocess import Popen, PIPE, DEVNULL
import requests
import time

logger = logging.getLogger(__name__)


class Connection:
    """Low-level Joern HTTP connection manager.

    This class is private and subject to change. Use JoernConnection from _lifecycle instead.
    """
    def __init__(self, joern_server: str = ""):
        self.proc = None
        self.joern_server = joern_server or "http://localhost:8080"
        self.session = requests.Session()
        self.start()

    def sendQuery(self, query: str):
        logger.debug(f"Sending query to Joern: {query[:100]}...")
        response = self.session.post(
            f"{self.joern_server}/query-sync", 
            json={"query": query}
        )
        response.raise_for_status()
        logger.debug(f"Received response from Joern: {response.text[:100]}...")   
        return response.json().get("stdout", "")

    def _wait_for_server(self, timeout: int = 60):
        """Wait for an already-running Joern server to be reachable."""
        logger.debug(f"Waiting for Joern server at {self.joern_server}...")
        start_time = time.time()
        while True:
            try:
                self.session.get(self.joern_server, timeout=1)
                logger.debug("Joern server is reachable.")
                return
            except requests.exceptions.RequestException:
                if time.time() - start_time > timeout:
                    raise RuntimeError(f"Joern server at {self.joern_server} failed to become reachable within {timeout}s.")
                time.sleep(1)

    def start(self, timeout: int = 60):
        """Start a new Joern Server process."""
        logger.debug("Starting Joern server process...")
        argv = ['joern', '--server']

        self.proc = Popen(argv,
                          stdin= DEVNULL,
                          stdout=DEVNULL,
                          stderr=PIPE,
                          text=True)

        self._wait_for_server(timeout=timeout)

    def stop(self):
        """Terminate the Joern process."""
        if self.proc:
            logger.debug("Terminating Joern process.")
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.terminate()
            self.proc.wait()
            self.session.close()
            self.proc = None
