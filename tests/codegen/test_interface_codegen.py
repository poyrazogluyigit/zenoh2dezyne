"""Tests for the per-unit StateMachine -> Interface translation in codegen.codegen."""
import re
import unittest

from src.datatypes import StateMachine, State, OutEvent, DeferTo, ChangeStateTo
from src.codegen.codegen import state_machines_to_code


def _normalize(text: str) -> str:
    """Collapse whitespace so structural comparisons ignore formatting drift."""
    return re.sub(r"\s+", " ", text).strip()


class TestStateMachinesToCode(unittest.TestCase):
    def test_single_thread_emits_interface_and_component(self):
        sms = {
            "main": StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [OutEvent("basic/B/A")], [ChangeStateTo(1)]),
            ])
        }
        name, file, _ = state_machines_to_code("A", sms)
        code = file.to_code()

        self.assertEqual(name, "A")
        self.assertIn("interface IA", code)
        self.assertIn("component CA", code)
        self.assertIn("provides IA A_top;", code)
        self.assertIn("import Step.dzn;", code)
        # Topic mangling: '/' -> '_'
        self.assertIn("out void basic_B_A();", code)
        self.assertIn("in void step();", code)
        self.assertIn("basic_B_A;", code)  # Action in state body

    def test_subint_state_per_thread(self):
        sms = {
            "main": StateMachine([State(1, [], []), State(2, [], []), State(3, [], [])])
        }
        _, file, _ = state_machines_to_code("A", sms)
        code = file.to_code()
        self.assertIn("subint State_main { 1..3 };", code)
        self.assertIn("State_main s_main = 1;", code)

    def test_multi_successor_emits_one_guard_per_successor_with_signals(self):
        sms = {
            "main": StateMachine([
                State(1, [], [ChangeStateTo(2), ChangeStateTo(3)]),
                State(2, [], []),
                State(3, [], []),
            ])
        }
        _, file, _ = state_machines_to_code("X", sms)
        code = file.to_code()
        # Branch signal events are declared for each (source, target).
        self.assertIn("out void main_branch_1_to_2();", code)
        self.assertIn("out void main_branch_1_to_3();", code)
        # Two sibling guards for state 1: each fires its branch signal then transitions.
        self.assertRegex(code, r"\[s_main == 1\]\s*\{\s*main_branch_1_to_2;\s*s_main = 2;\s*\}")
        self.assertRegex(code, r"\[s_main == 1\]\s*\{\s*main_branch_1_to_3;\s*s_main = 3;\s*\}")

    def test_single_successor_does_not_emit_branch_signal(self):
        sms = {
            "main": StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [], []),
            ])
        }
        _, file, _ = state_machines_to_code("X", sms)
        code = file.to_code()
        self.assertNotIn("main_branch_", code)
        self.assertRegex(code, r"\[s_main == 1\]\s*s_main = 2;")

    def test_callback_in_event_declared_and_triggered(self):
        sms = {
            "main": StateMachine([State(1, [DeferTo("main")], [])]),
            "cb": StateMachine([State(1, [DeferTo("main")], [])]),
        }
        callback_topics = {"cb": "basic/B/A"}
        _, file, _ = state_machines_to_code("B", sms, callback_topics)
        code = file.to_code()
        # The subscribed topic becomes an in-event declaration.
        self.assertIn("in void basic_B_A();", code)
        # And drives a trigger that switches to the callback when on main.
        self.assertRegex(
            re.sub(r"\s+", " ", code),
            r"on basic_B_A: \{ \[thread == main\] \{ thread = cb; s_cb = 1; \} \[otherwise\] \{\} \}",
        )

    def test_terminal_state_emits_empty_block(self):
        sms = {
            "main": StateMachine([
                State(1, [], [ChangeStateTo(2)]),
                State(2, [DeferTo("main")], []),  # terminal DeferTo to own thread
            ])
        }
        _, file, _ = state_machines_to_code("A", sms)
        code = _normalize(file.to_code())
        # On main, DeferTo('main') is a no-op: render an empty block.
        self.assertIn("[s_main == 2] {}", code)

    def test_callback_defer_to_main_emits_thread_assignment_and_reset(self):
        sms = {
            "main": StateMachine([State(1, [DeferTo("main")], [])]),
            "callback": StateMachine([
                State(1, [OutEvent("basic/A/B")], [ChangeStateTo(2)]),
                State(2, [DeferTo("main")], []),
            ]),
        }
        _, file, _ = state_machines_to_code("B", sms)
        code = _normalize(file.to_code())

        # Enum lists both threads with main first
        self.assertIn("enum CurrentExecutionThread { main, callback };", code)
        # Callback's terminal state assigns thread=main and resets s_callback=1
        self.assertRegex(code, r"\[s_callback == 2\]\s*\{\s*thread = main;\s*s_callback = 1;\s*\}")

    def test_main_always_first_in_enum(self):
        sms = {
            "z_callback": StateMachine([State(1, [], [])]),
            "main": StateMachine([State(1, [], [])]),
            "a_callback": StateMachine([State(1, [], [])]),
        }
        _, file, _ = state_machines_to_code("U", sms)
        code = file.to_code()
        # main is first regardless of insertion order
        m = re.search(r"enum CurrentExecutionThread \{ ([^}]+) \};", code)
        self.assertIsNotNone(m)
        self.assertTrue(m.group(1).strip().startswith("main"))

    def test_outgoing_events_are_unique(self):
        sms = {
            "main": StateMachine([
                State(1, [OutEvent("foo/bar")], [ChangeStateTo(2)]),
                State(2, [OutEvent("foo/bar")], [ChangeStateTo(1)]),  # duplicate
            ])
        }
        _, file, _ = state_machines_to_code("A", sms)
        code = file.to_code()
        self.assertEqual(code.count("out void foo_bar();"), 1)


if __name__ == "__main__":
    unittest.main()
