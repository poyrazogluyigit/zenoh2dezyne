import logging
from builder import Builder
from datatypes import ControlFlowGraph, CallbackThread, MainThread, TranslationUnit, VarPublisher, SessPublisher
from dezyne_structs import DezyneComponent, DezyneInterface, DezyneBehavior, DezyneBehaviorStatement, DezyneGuard, DezyneTrigger
from pathlib import Path

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
        self.fetchConnections(translation_units)
        self.generateStepper()
        self.generateNetworkElement(single_stepper)
        self.generateTopModel()
        
    def printToOutput(self):
        '''Flush generated files to output directory.'''
    
    def fetchConnections(self, units: list[TranslationUnit]):
        '''Construct a connection graph corresponding to keyexpr connections between nodes.'''
        ...

    def generateUnitModel(self, unit: TranslationUnit) -> DezyneComponent:
        interface = DezyneInterface(
            name=unit.file_name,
            in_events = [i.key_expr for i in unit.callback_threads],
            out_events = [i.key_expr for i in unit.var_publishers] 
            + [expr for i in unit.sess_publishers for expr in i.key_exprs],
            behavior=self.generateBehavior(unit)
        )
        return DezyneComponent(
            name=unit.filename,
            provides=[interface],
            requires=[]
        )  
      
    '''
    0. kac cfg varsa ona gore possible executions olustur
    1. her cfg icin:
        1. cfg sinde kac state varsa ona gore state degiskeni olustur
        2. cfg sinde kac state varsa o kadar DezyneBehaviorStatement olustur
        3. cfg'deki her node'u 1'den itibaren numaralandir
        4. her bir node icin:
            1. eger icinde put event varsa DezyneAction olustur
            2. DezyneVarSet olustur (stateVar, number of next State)
            3. rhs = [DezyneAction, DezyneVarSet]
            4. eger return node'su ise rhs'ye possible executions setleme ekle
        5. branch = DezyneBehaviorStatement(possible execution == cfg, [her node icin olusturulan DezyneBehaviorStatement])
    2. state degiskeni initializationlari
    3. actions = DezyneBehaviorStatement(on step, [her cfg icin olusturulan branch'ler])
    4. DezyneBehavior(state degiskenleri, [possible executions + initializationlar + actions])
    '''

    def generateBehaviorForCFG(self, cfg: ControlFlowGraph):
        ...

    def generateBehavior(self, unit: TranslationUnit):
        cfgs = [unit.main_thread.cfg] + [cb.cfg for cb in unit.callback_threads]
        branches = []
        for cfg in cfgs:
            statements = []
            for node in cfg:
                if node.is_put:
                    # create DezyneAction for put event
                    pass
                if node.is_return:
                    # return execution to main if in callback
                    pass
                for succ in node.successors:
                    # create DezyneVarSet for state transition
                    pass
            branch = DezyneBehaviorStatement(
                lhs=DezyneGuard(...),
                rhs=statements
            )
            branches.append(branch)
        # create initialization statements for state variables
        # create possible execution statements
        # create on step statements for branches
        behavior_statement_part = DezyneBehaviorStatement(
            lhs=DezyneTrigger("step"),
            rhs=branches
        )
        return DezyneBehavior(...)

    def generateStepper(self):
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
        self.stepper = DezyneComponent(
            name="Step",
            provides = [interface],
            requires=[]
        ) if self.stepper is None else self.stepper
    
    def generateNetworkElement(self, single_stepper = False):
        ...
    
    def generateTopModel(self):
        ...



if __name__ == "__main__":
    codegen = CodeGenerator("pgm-no-zenoh")
    codegen.generate()