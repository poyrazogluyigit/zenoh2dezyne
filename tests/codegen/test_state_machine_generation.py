import unittest

import networkx as nx

from src.datatypes import StateMachine, State, OutEvent, DeferTo, ChangeStateTo

from src.codegen._behavior import _generate_behavior_for_cfg, _generate_behavior
from ..mock_data import mock_translation_unit


def _state_machine_to_graph(sm: StateMachine) -> nx.DiGraph:
    graph = nx.DiGraph()
    for state in sm.states:
        stmt_signature = tuple(sorted(
            (type(stmt).__name__, getattr(stmt, "key_expr", None), getattr(stmt, "target_execution", None))
            for stmt in state.statements
        ))
        graph.add_node(state.value, statements=stmt_signature, out_degree=len(state.state_changes))
    for state in sm.states:
        for change in state.state_changes:
            graph.add_edge(state.value, change.target_state)
    return graph


def _state_machines_isomorphic(actual: StateMachine, expected: StateMachine) -> bool:
    actual_graph = _state_machine_to_graph(actual)
    expected_graph = _state_machine_to_graph(expected)
    matcher = nx.algorithms.isomorphism.DiGraphMatcher(
        actual_graph,
        expected_graph,
        node_match=lambda a, b: (
            a["statements"] == b["statements"]
            and a["out_degree"] == b["out_degree"]
        ),
    )
    return matcher.is_isomorphic()


class TestStateMachineGeneration(unittest.TestCase):
    
    def test_behavior_generation_for_cfg(self):
        output = StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [OutEvent("example/topic/var_out")], [ChangeStateTo(3)]), 
                State(3, [OutEvent("example/topic/session_out")], [ChangeStateTo(4)]),
                State(4, [DeferTo("main")], [])
            ])
        data = mock_translation_unit
        cfg = data.callback_threads[0].cfg
        sm = _generate_behavior_for_cfg(data, cfg)
        self.assertTrue(_state_machines_isomorphic(sm, output))

    def test_behavior_generation(self):
        output = {
            "main": StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [], [ChangeStateTo(3), ChangeStateTo(5)]),
                State(3, [OutEvent("example/topic/var_out")], [ChangeStateTo(4)]),
                State(4, [OutEvent("example/topic/session_out")], [ChangeStateTo(3), ChangeStateTo(5)]),
                State(5, [DeferTo("main")], []) # TODO defer to logic is not correct
            ]),
            "callback": StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [OutEvent("example/topic/var_out")], [ChangeStateTo(3)]), 
                State(3, [OutEvent("example/topic/session_out")], [ChangeStateTo(4)]),
                State(4, [DeferTo("main")], [])
            ])
        }
        sm = _generate_behavior(mock_translation_unit)
        self.assertEqual(set(sm.keys()), set(output.keys()))
        for name, expected_sm in output.items():
            self.assertTrue(_state_machines_isomorphic(sm[name], expected_sm))
    