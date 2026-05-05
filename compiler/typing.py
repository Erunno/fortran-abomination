class Type:
    pass

class TerminalType(Type):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"T_{self.name}"
class ArrayType(Type):
    def __init__(self, element_type: Type, spec_ast):
        self.element_type = element_type
        self.spec_ast = spec_ast

    def __str__(self):
        return f"{str(self.element_type)}[]"

