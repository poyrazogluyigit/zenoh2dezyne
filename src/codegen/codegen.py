import logging
from graphutils import JoernCFG

from ..datatypes import TranslationUnit
from ._behavior import _generate_unit_model, _generate_stepper, _generate_network_elt, _generate_top_model

logger = logging.getLogger(__name__)

def _generate_unit_model( unit: TranslationUnit) -> DezyneComponent:
    interface = DezyneInterface(
        name=unit.file_name,
        in_events = [i.key_expr for i in unit.callbacks],
        out_events = [i.key_expr for i in unit.var_publishers] 
        + [expr for i in unit.sess_publishers for expr in i.key_exprs],
        behavior=...
    )
    return DezyneComponent(
        name=unit.file_name,
        provides=[interface],
        requires=[]
    )


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
    def generate(self, translation_units: list[TranslationUnit], single_stepper = False):
        self.nodes = [self.generateUnitModel(unit) for unit in translation_units]
        stepper = _generate_stepper()
        netelem = _generate_network_elt(single_stepper)
        top = _generate_top_model()
        
    def printToOutput(self):
        '''Flush generated files to output directory.'''
        ...