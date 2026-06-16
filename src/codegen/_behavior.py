from ..graphutils import JoernCFG
from ..datatypes import TranslationUnit, State, OutEvent, DeferTo, ChangeStateTo, StateMachine


def _generate_behavior_for_cfg(translation_unit, cfg: JoernCFG) -> StateMachine:
    '''Generate a behavior for a given CFG.

    The CFG must already be normalized (publish nodes tagged with neutral
    ``comm_op``/``topic`` attributes by ``builders._normalize``); this function
    reads only those neutral attributes and carries no middleware knowledge.
    '''
    stmts = []
    for node_id in cfg:
        state = State(value=node_id, state_changes=[ChangeStateTo(succ) for succ in cfg.get_successors(node_id)])
        # TODO change DeferTo
        if cfg.get_type(node_id) == "METHOD_RETURN":
            state.statements.append(DeferTo("main"))
        elif cfg.get_data(node_id, "comm_op") == "publish":
            state.statements.append(OutEvent(cfg.get_data(node_id, "topic")))
        stmts.append(state)
    return StateMachine(states=stmts)

def _generate_behavior(unit: TranslationUnit) ->dict[str, StateMachine]:
    state_machines = dict()
    for thread in [unit.main_thread] + unit.callback_threads:
        state_machine = _generate_behavior_for_cfg(unit, thread.cfg)
        state_machines[thread.name] = state_machine
    return state_machines
    