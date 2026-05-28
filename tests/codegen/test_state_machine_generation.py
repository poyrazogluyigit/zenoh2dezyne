import unittest
from src.datatypes import StateMachine, State, OutEvent, DeferTo, ChangeStateTo

from src.codegen._behavior import _generate_behavior_for_cfg, _generate_behavior
from ..mock_data import mock_translation_unit


class TestStateMachineGeneration(unittest.TestCase):
    
    def test_behavior_generation_for_cfg(self):
        output = StateMachine([
                State(1, [ChangeStateTo(2)]),
                State(2, [OutEvent("example/topic/var_out"), ChangeStateTo(3)]), 
                State(3, [OutEvent("example/topic/session_out"), ChangeStateTo(4)]),
                State(4, [DeferTo("main")])
            ])
        data = mock_translation_unit
        cfg = data.callbacks[0].cfg
        sm = _generate_behavior_for_cfg(data, cfg)
        self.assertEqual(sm, output)

    def test_behavior_generation(self):
        output = {
            "callback": StateMachine([
                State(1, [ChangeStateTo(2)]),
                State(2, [OutEvent("example/topic/var_out"), ChangeStateTo(3)]), 
                State(3, [OutEvent("example/topic/session_out"), ChangeStateTo(4)]),
                State(4, [DeferTo("main")])
            ]),
            "main": StateMachine([
                State(1, [ChangeStateTo(2)]),
                State(2, [ChangeStateTo(3), ChangeStateTo(5)]),
                State(3, [ChangeStateTo(4), OutEvent("example/topic/var_out")]),
                State(4, [ChangeStateTo(3), ChangeStateTo(5), OutEvent("example/topic/session_out")]),
                State(5, [])
            ])
        }
        sm = _generate_behavior(mock_translation_unit)
        self.assertEqual(sm, output)
    