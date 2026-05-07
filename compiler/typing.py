from compiler.debugging.color_printer import Colors as c
class Type:
    pass

class TerminalType(Type):
    def __init__(self, name):
        self.name = name

    def get_dim_count(self):
        return 0

    def __str__(self):
        return f"{c.TYPE}T_{self.name}{c.END}"
class ArrayType(Type):
    def __init__(self, element_type: Type, spec_ast):
        self.element_type = element_type
        self.spec_ast = spec_ast

    def get_dim_count(self):
        return 1 + self.element_type.get_dim_count()

    def __str__(self):
        return f"{str(self.element_type)}{c.TYPE}[]{c.END}"

