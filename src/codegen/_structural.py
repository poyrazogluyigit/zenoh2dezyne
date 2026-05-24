from ..datatypes import DezyneInterface, DezyneComponent, DezyneBehavior, DezyneBehaviorStatement, DezyneTrigger

def _generate_stepper() -> DezyneComponent:
    interface = DezyneInterface(
        name="Step",
        in_events=[],
        out_events=["step"],
        behavior=DezyneBehavior(
            state_vars=[],
            statements=[DezyneBehaviorStatement(
                lhs=DezyneTrigger("inevitable"),
                rhs=["step"]
            )]
        )
    )
    return DezyneComponent(
        name="Step",
        provides = [interface],
        requires=[]
    )

def _generate_network_elt(single_stepper = False):
    ...

def _generate_top_model():
    ...