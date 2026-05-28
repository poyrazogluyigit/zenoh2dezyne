from typing import Any
import json
import re
import logging

logger = logging.getLogger(__name__)

def _parse_joern_json(response: str) -> Any:
    """Parse Joern's JSON response, stripping ANSI codes and extracting JSON.
    
    Args:
        response: Raw response from Joern server
        
    Returns:
        Parsed JSON object
        
    Raises:
        ValueError: If response cannot be parsed as valid JSON
    """
    rhs = _clean_joern_repl(response)
    logger.debug(f"Cleaning json: {rhs}")

    if rhs.startswith('"""') and rhs.endswith('"""'):
        rhs = rhs[3:-3].strip()
    elif rhs.startswith('"') and rhs.endswith('"'):
        rhs = rhs[1:-1].encode("utf-8").decode("unicode_escape").strip()

    match = re.search(r'([\[\{].*[\]\}])', rhs, re.DOTALL)
    if match:
        rhs = match.group(1)

    try:
        clean = json.loads(rhs)
        logger.debug(f"Cleaned json: {clean}")
        return clean
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse Joern JSON: {exc}") from exc
    
def _clean_joern_repl(response: str) -> str:
    logger.debug(f"Cleaning repl: {response}")
    clean_resp = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', response)
    rhs = clean_resp.split("=", 1)[-1].strip() if "=" in clean_resp else clean_resp.strip()
    logger.debug(f"Cleaned: {rhs}")
    return rhs
