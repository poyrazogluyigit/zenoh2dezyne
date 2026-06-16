from ..graphutils import JoernCFG
from ..datatypes import TranslationUnit, State, OutEvent, DeferTo, ChangeStateTo, StateMachine


def _generate_behavior_for_cfg(translation_unit, cfg: JoernCFG) -> StateMachine:
    '''Generate a behavior for a given CFG.'''
    stmts = []
    for node_id in cfg:
        state = State(value=node_id, state_changes=[ChangeStateTo(succ) for succ in cfg.get_successors(node_id)])
        # TODO change DeferTo
        if cfg.get_type(node_id) == "METHOD_RETURN":
            state.statements.append(DeferTo("main"))
        elif cfg.get_type(node_id) == "put" and cfg.get_data(node_id, "put_target") == "session":
            topic = cfg.get_data(node_id, "put_topic")
            state.statements.append(OutEvent(topic))
        elif cfg.get_type(node_id) == "put":
            var_name = cfg.get_data(node_id, "put_target")
            publisher = next((p for p in translation_unit.publishers if p.symbol == var_name), None)
            if publisher is None:
                raise ValueError(f"Expected to find a publisher for variable {var_name}")
            state.statements.append(OutEvent(publisher.topic))
        stmts.append(state)
    return StateMachine(states=stmts)

def _generate_behavior(unit: TranslationUnit) ->dict[str, StateMachine]:
    state_machines = dict()
    for thread in [unit.main_thread] + unit.callback_threads:
        state_machine = _generate_behavior_for_cfg(unit, thread.cfg)
        state_machines[thread.name] = state_machine
    return state_machines
    