import logging

from ..graphutils import JoernCFG
from ..builders import InterconnectionGraph

from ..datatypes import StateMachine

from _behavior import _generate_behavior

logger = logging.getLogger(__name__)

def events_to_code():
    ...

def state_machines_to_code(state_machines: dict[str, StateMachine]) -> dict[str, str]:
    '''Convert the given state machines to Dezyne code.'''
    threads = state_machines.keys()
    thread_enum = TypeDecl('enum', 'CurrentExecutionThread', threads)
    thread_state_variables = [TypeDecl('subint', sm.num_states) for sm in state_machines.values()]
    bhv = Behavior(state_machines, thread_control_variable_type='CurrentExecutionThread', **thread_state_variables)
    return Interface(thread_enum, thread_state_variables, bhv)

def generate_network_element(model: InterconnectionGraph, unit_models: list[Interface], stepper: Interface) -> Interface:
    ...

def generate_top_model(model: InterconnectionGraph, unit_models: list[Interface], stepper: Interface, network_element: Interface) -> Interface:
    ...

def generate_file(interface: Interface, file_name: str):
    return File(interface, generate_component(interface))
    

class CodeGenerator:
    def __init__(self, output_dir: str = "."):
        self.nodes = []
        self.output_dir = output_dir
        self.stepper = None
        self.networkElement = None
        self.topModel = None
        ...

        '''
        0. her bir translation unit icin:
            1. o unitin kendi dosyasini generatele
            2. hangi unitlerle baglantisi oldugunu bul
            3. bu bilgiyi bir graph yapisina kaydet?
        1. stepper modeli generatele
        2. connection graph ve stepper kullanarak network elementi generatele
        3. top modeli generatele

        '''
    def generate(self, model: InterconnectionGraph, single_stepper = False):
        '''Generate Dezyne code from the given model.'''
        unit_models = dict()
        for unit in model:
            state_machines = _generate_behavior(unit['data'])
            name, file = state_machines_to_code(state_machines)
            unit_codes[name] = file
        stepper = generate_stepper(model, single_stepper)
        network_element = generate_network_element(model, unit_models, stepper)
        generate_top_model(model, unit_models, stepper, network_element)
        return unit_models, stepper, network_element
        
    def printToOutput(self):
        '''Flush generated files to output directory.'''
        ...