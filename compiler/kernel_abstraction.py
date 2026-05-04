from compiler.context import LocalContext
from compiler.fparser_tree_abstraction import FparserTree

class Kernel:
    pass

class KernelFunctionDefinition:
    def __init__(self, kernel_ast):
        self.full_tree = FparserTree(kernel_ast)
        
        self.declaration_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Subroutine_Stmt")[0])
        self.specification_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Specification_Part")[0])
        self.code_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Execution_Part")[0])

        self.local_context = LocalContext(self.specification_ast)

    def name(self):
        return str(self.declaration_ast.get_all_nodes_in_children_of_type("Name")[0])
   

    

