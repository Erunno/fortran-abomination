from compiler.context import Context
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.debugging.color_printer import Colors as c
from compiler.expression_walking.visitor_base import AstVisitor
from compiler.fparser_tree_abstraction import FparserTree
from compiler.kernel_abstraction import Kernel


class CppExprCodeGenerator(AstVisitor):
    def __init__(self, variable_name_generator=VariableNamer()):
        self.var_namer = variable_name_generator

    def generate_cpp_code(self, kernel: Kernel) -> str:
        code_lines = self._visit_all_code_lines_of(kernel)
        return "\n".join(code_lines)
    
    def generate_cpp_code_for_ast(self, ast, context) -> str:
        return self._visit(ast, context)

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

        dim_sizes_variable_names = self.var_namer.get_get_dim_sizes_variable_names_of(name_node, context)

        return f"{name_part_code}[IDX({', '.join(subscripts)}, {', '.join(dim_sizes_variable_names)})]"

    @AstVisitor.accept("Name")
    def _visit_name(self, node, context) -> str:
        return self.var_namer.get_name(node, context)
    
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
    
    @AstVisitor.accept("Intrinsic_Function_Reference")
    def _visit_intrinsic_function_reference(self, node, context) -> str:
        node = FparserTree(node)

        name = str(node.get_first_child_of_type("Intrinsic_Name")).lower()

        if name == "size":
            arr_name, arg_num = node.get_all_nodes_in_children_of_type("Actual_Arg_Spec_List")[0].children
            arr_name = str(arr_name)
            arg_num = int(str(arg_num))

            dim_sizes_variable_names = self.var_namer.get_get_dim_sizes_variable_names_of(arr_name, context)
            return dim_sizes_variable_names[arg_num - 1]

        return self._default_visit(node.tree, context)

