import unittest
from src.graphutils import JoernCFG
from src.datatypes._structs import StateMachine, State, OutEvent, DeferTo, ChangeStateTo

from src.codegen._behavior import _generate_state_change, _generate_from_content, _generate_behavior_for_cfg, _generate_behavior
from ..mock_data import mock_translation_unit


class TestBehaviorGeneration(unittest.TestCase):

    def test_state_change_generation(self):
        data = mock_translation_unit
        cfg = data.callbacks[0].cfg

        # sub cases
        with self.subTest("Single out edge from a node"):
            node = next((node for node in cfg if cfg.graph.out_degree(node) == 1), None)
            self.assertIsNotNone(node, "Expected to find a node with a single out edge")
            succ = cfg.get_successors(node.id)[0]
            output = _generate_state_change(node)
            self.assertEqual(output, [ChangeStateTo(succ.id)])
        
        with self.subTest("Multiple out edges from a node"):
            node = next((node for node in cfg if cfg.graph.out_degree(node) > 1), None)
            self.assertIsNotNone(node, "Expected to find a node with multiple out edges")
            succs = cfg.get_successors(node.id)
            output = _generate_state_change(node)
            self.assertEqual(output, [ChangeStateTo(succ.id) for succ in succs])
        
        with self.subTest("No out edges from a node"):
            node = next((node for node in cfg if data.callbacks[0].cfg.graph.out_degree(node) == 0), None)
            self.assertIsNotNone(node, "Expected to find a node with no out edges")
            output = _generate_state_change(node)
            self.assertEqual(output, [])
    

    def test_generate_from_content(self):
        data = mock_translation_unit
        cfg = data.callbacks[0].cfg

        # sub cases
        with self.subTest("Put statement from a variable publisher"):
            var_put_node = next((node for node in cfg if node.data['code'] == 'A_pub.put("example payload to A")'), None)
            self.assertIsNotNone(var_put_node, "Expected to find put in CFG")
            output = _generate_from_content(data, var_put_node)
            self.assertEqual(output, OutEvent("example/topic/var_out"))

        with self.subTest("Put statement from a session publisher"):
            sess_put_node = next((node for node in cfg if node.data['code'] == 'session.put("example/topic/session_out", "example payload to session")'), None)
            self.assertIsNotNone(sess_put_node, "Expected to find session put in CFG")
            output = _generate_from_content(data, sess_put_node)
            self.assertEqual(output, OutEvent("example/topic/session_out"))

        with self.subTest("Method return statement"):
            return_node = next((node for node in cfg if node.data['node_type'] == 'METHOD_RETURN'), None)
            self.assertIsNotNone(return_node, "Expected to find method return in CFG")
            output = _generate_from_content(data, return_node)
            self.assertEqual(output, DeferTo("main"))

    
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
            "callback": StateMachine[
                State(1, [ChangeStateTo(2)]),
                State(2, [OutEvent("example/topic/var_out"), ChangeStateTo(3)]), 
                State(3, [OutEvent("example/topic/session_out"), ChangeStateTo(4)]),
                State(4, [DeferTo("main")])
            ],
            "main": StateMachine(...)
        }
        sm = _generate_behavior(mock_translation_unit)
        self.assertEqual(sm, output)
    