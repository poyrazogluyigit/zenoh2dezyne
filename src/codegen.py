import logging
from builder import Builder
from datatypes import *
from pathlib import Path

logger = logging.getLogger(__name__)



class CodeGenerator:
    def __init__(self, output_dir: str = ""):
        self.nodes = []
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
    def generate(self, builder: Builder, single_stepper = False):
        translation_units = builder.translation_units
        self.nodes = [self.generateUnitModel(unit) for unit in translation_units]
        self.fetchConnections(translation_units)
        if self.stepper is None:
            self.generateStepper()
        self.generateNetworkElement(single_stepper)
        self.generateTopModel()
        
    def printToOutput(self):
        '''Flush generated files to output directory.'''
    
    def fetchConnections(self, units: list[TranslationUnit]):
        '''Construct a connection graph corresponding to keyexpr connections between nodes.'''
        ...

    def generateUnitModel(self, unit: TranslationUnit) -> DezyneFile:
        ...

    def generateStepper(self):
        ...
    
    def generateNetworkElement(self, single_stepper = False):
        ...
    
    def generateTopModel(self):
        ...



if __name__ == "__main__":
    codegen = CodeGenerator("pgm-no-zenoh")
    codegen.generate_code()