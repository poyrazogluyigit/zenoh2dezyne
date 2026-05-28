import logging

from ..graphutils import JoernCFG
from ..datatypes import TranslationUnit

logger = logging.getLogger(__name__)

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
        ...
        
    def printToOutput(self):
        '''Flush generated files to output directory.'''
        ...