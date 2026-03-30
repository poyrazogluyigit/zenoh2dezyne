import logging
from builder import Builder
from containers import *
from pathlib import Path

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, project_name: str, output_dir: str = "", joern_server: str = ""):
        self.builder = Builder(joern_server)
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        self.indent_amt = 0

    def fetch_units(self):
        logger.debug(f"Fetching units for project '{self.project_name}'")
        self.units = list(self.builder.buildDict(self.project_name).values())

    def generate_code(self):
        logger.debug("Generating code from units")
        self.fetch_units()
        logger.debug(f"Ensuring output directory exists: {self.output_dir}")
        Path.mkdir(self.output_dir, parents=True, exist_ok=True)
        for unit in self.units:
            out_file = self.output_dir / (unit.filename.rsplit('.', 1)[0] + ".dzn")
            logger.debug(f"Writing generated code for unit to: {out_file}")
            with open(out_file, "w") as f:
                f.write(self.generate_unit_code(unit))

    def indent(self, code: str):
        return "\t" * self.indent_amt + code

    # TODO pub/sub names will change, you need to preserve some 
    # kind of mapping
    # TODO putstmts might need to transform into behavioral blocks
    def generate_unit_code(self, unit: Unit):
        # definitions
        code = f"interface {unit.filename.rsplit('.', 1)[0]} {{\n"
        self.indent_amt += 1
        for sub in unit.subscribers:
            code += self.indent(f"in void {sub.keyExpr};\n")
        for pub in unit.publishers:
            code += self.indent(f"out void {pub.keyExpr};\n")
        # behavioral block
        code += self.indent("behavior {\n")
        self.indent_amt += 1
        for sub in unit.subscribers:
            code += self.indent(f"on {sub.keyExpr}: {{\n")
            self.indent_amt += 1
            for putStmt in sub.putStmts:
                code += self.translate_control_flow(putStmt)
            self.indent_amt -= 1
            code += self.indent("}\n")
        self.indent_amt -= 1
        code += self.indent("}\n")
        self.indent_amt -= 1        
        code += "}"
        return code
    
    def indentStmts(self, code: list[str]):
        self.indent_amt += 1
        code = [self.indent(i) for i in code]
        self.indent_amt -= 1

    # control flow traversal occurs from bottom to top, so else statements are parsed before
    # if statements
    # FIXME current issues:
    # multiplicity of if statements not checked:
    #       if a, b occur on two branches of a single control statement, the 
    #       control statement is printed twice
    # no control flow simplification
    #       if only 'else' is relevant on a compound statement,
    #       simplify to 'if not'
    def translate_control_flow(self, putStmt: PutStmt):
        code = [self.indent(f"{putStmt.keyExpr}();\n")]
        isCompound = False
        for flowStmt in putStmt.controlFlow:
            (stmtType, stmtCondition), = flowStmt.items()
            if stmtType == 'IF' and not isCompound:
                self.indentStmts(code)
                code.insert(0, self.indent(f"if ({stmtCondition})" "{\n"))
                code.append(self.indent("}\n"))
            elif stmtType == "IF" and isCompound:
                code.insert(0, self.indent(f"if ({stmtCondition})" "{}\n"))
                isCompound = False
            elif stmtType == 'ELSE':
                self.indentStmts(code)
                code.insert(0, self.indent("else {\n"))
                code.append(self.indent("}\n"))
                isCompound = True
        return "".join(code)



if __name__ == "__main__":
    codegen = CodeGenerator("pgm-no-zenoh")
    codegen.generate_code()