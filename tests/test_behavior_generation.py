import unittest
from src.graphutils import JoernCFG, CFGNode

from src.codegen._behavior import _generate_behavior_for_cfg, _generate_external_actions
from .example_dotcfgs import looping_callback, empty_callback, branching_callback

class TestBehaviorGeneration(unittest.TestCase):
    ...
    