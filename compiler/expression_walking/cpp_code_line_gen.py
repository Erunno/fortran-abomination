from compiler.context import Context
from compiler.debugging.color_printer import Colors as c
from compiler.expression_walking.visitor_base import AstVisitor
from compiler.fparser_tree_abstraction import FparserTree
from compiler.kernel_abstraction import Kernel

class FromContextNamer:
    def get_name(self, node, context: Context) -> str:
        if node.__class__.__name__.lower() == "name":
            return self.get_name_from_name_node(node, context)
        else:
            raise Exception(f"Unsupported node type {c.CLASS}{node.__class__.__name__}{c.END} for naming. Function at: {__file__}")

    def get_name_from_name_node(self, name_node, context: Context) -> str:
        original_name_used_in_context = str(name_node)
        variable = context.get_variable_by_name(original_name_used_in_context)
        
        real_variable_name = variable.name()
        return real_variable_name
    
    def get_get_dim_sizes_variable_names_of(self, name_node, context: Context) -> list[str]:
        original_name_used_in_context = str(name_node)
        variable = context.get_variable_by_name(original_name_used_in_context)
        
        dim_count = variable.type().get_dim_count()
        return [f"{variable.name()}_dim{dim_num + 1}" for dim_num in range(dim_count)]

class CppCodeGenerator(AstVisitor):
    def __init__(self, variable_name_generator=FromContextNamer()):
        self.variable_name_generator = variable_name_generator

    def generate_cpp_code(self, kernel: Kernel) -> str:
        code_lines = self._visit_all_code_lines_of(kernel)
        return "\n".join(code_lines)
    
    @AstVisitor.accept("Assignment_Stmt")
    def _visit_assignment_stmt(self, node, context) -> str:
        to_node, _, from_node = node.children

        to_str = self._visit(to_node, context)
        from_str = self._visit(from_node, context)

        return f"{to_str} = {from_str};"

    @AstVisitor.default_visit()
    def _visit_default(self, node, context) -> str:
        print(f"{c.WARN}!!! Warning !!!{c.END} No specific visit method for node type {c.CLASS}{node.__class__.__name__}{c.END}. Function at: {__file__}")
        return f"{c.ERR}<str(node)={str(node)}>{c.END}"
    
    @AstVisitor.accept("Part_ref")
    def _visit_part_ref(self, node, context) -> str:
        name_node = FparserTree(node).get_first_child_of_type("Name")
        subscript_nodes = FparserTree(node).get_first_child_of_type("Section_Subscript_List")
        
        name_part_code = self._visit(name_node, context)
        subscripts = [self._visit(subscript, context) for subscript in FparserTree(subscript_nodes).children()]

        dim_sizes_variable_names = self.variable_name_generator.get_get_dim_sizes_variable_names_of(name_node, context)

        return f"{name_part_code}[IDX({', '.join(subscripts)}, {', '.join(dim_sizes_variable_names)})]"

    @AstVisitor.accept("Name")
    def _visit_name(self, node, context) -> str:
        return self.variable_name_generator.get_name(node, context)
    
    @AstVisitor.accept("Level_2_Expr")
    def _visit_level_2_expr(self, node, context) -> str:
        left_node, operator_node, right_node = node.children

        left_str = self._visit(left_node, context)
        right_str = self._visit(right_node, context)
        operator_str = str(operator_node)

        return f"({left_str} {operator_str} {right_str})"
    
    @AstVisitor.accept(
        "Int_Literal_Constant",
        "Real_Literal_Constant")
    def _visit_int_literal_constant(self, node, context) -> str:
        return str(node)