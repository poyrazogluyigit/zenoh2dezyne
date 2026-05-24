from ..graphutils import JoernCFG
from ..datatypes import TranslationUnit, State, OutEvent, DeferTo, ChangeStateTo, StateMachine

def _generate_state_change(node) -> list[ChangeStateTo]:
    for succ in node.successors:
        ...
        

def _generate_from_content(translation_unit, node) -> OutEvent | DeferTo | None:
    '''Generate behavior statements for a given CFG node.'''


def _generate_behavior_for_cfg(translation_unit, cfg: JoernCFG) -> StateMachine:
    '''Generate a behavior for a given CFG.'''
    sm = StateMachine()
    for node in cfg:
        state = State(value=node.id, statements=[])
        # Analyze the node and populate state.statements based on the CFG structure
        if node.is_put:
            ...
        elif node.is_method_return:
            ...
        sm.states.append(state)
    return sm

def _generate_behavior(unit: TranslationUnit) ->dict[str, StateMachine]:
    for thread in [unit.main_thread] + unit.callback_threads:
        num_states, stmts = _generate_behavior_for_cfg(thread.cfg)
        bhv = ()
    