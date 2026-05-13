from compiler.context import Variable
from compiler.expression_walking.visitor_base import AstVisitor
from compiler.fparser_tree_abstraction import FparserTree
from compiler.kernel_abstraction import Kernel

@AstVisitor.use_visit_all_children_as_default()
class UsedVarsFinder(AstVisitor):
    def find_used_vars(self, kernels: Kernel | list[Kernel]) -> list[Variable]:
        if not isinstance(kernels, list):
            kernels = [kernels]

        all_used_vars = set()
        for kernel in kernels:
            used_vars_in_kernel = self._find_in_one_kernel(kernel)
            all_used_vars.update(used_vars_in_kernel)

        return list(all_used_vars)

    def _find_in_one_kernel(self, kernel: Kernel) -> list[Variable]:
        used_in_code = self._visit_all_code_lines_of(kernel, post_process='flatten')
        used_in_do_stmts = self._visit_all_do_stmt_ranges_of(kernel, post_process='flatten')

        return list(set(used_in_code + used_in_do_stmts))

    @AstVisitor.accept("Name")
    def _visit_name(self, node, context) -> list[Variable]:
        var_name = str(node)
        return [context.get_variable_by_name(var_name)]

@AstVisitor.use_visit_all_children_as_default()
class UsedSizesFinder(AstVisitor):
    def find_all_used_sizes(self, kernel: Kernel) -> list[(Variable, int)]:
        used_in_code = self._visit_all_code_lines_of(kernel, post_process='flatten')
        used_in_do_stmts = self._visit_all_do_stmt_ranges_of(kernel, post_process='flatten')

        return list(set(used_in_code + used_in_do_stmts))

    @AstVisitor.accept("Intrinsic_Function_Reference")
    def _visit_intrinsic_function_reference(self, node, context) -> list[(Variable, int)]:
        node = FparserTree(node)

        name = str(node.get_first_child_of_type("Intrinsic_Name")).lower()
        if name != "size":
            return self._default_visit(node.tree, context)
        
        arr_name, arg_num = node.get_all_nodes_in_children_of_type("Actual_Arg_Spec_List")[0].children

        arr_name = str(arr_name)
        arg_num = int(str(arg_num))

        actual_var = context.get_variable_by_name(arr_name)
        return [(actual_var, arg_num)]
    
@AstVisitor.use_visit_all_children_as_default()
class WriteVarsFinder(AstVisitor):
    def find_variables_written_to(self, kernels: Kernel | list[Kernel]) -> list[Variable]:
        if not isinstance(kernels, list):
            kernels = [kernels]

        all_writes = []
        for kernel in kernels:
            writes = self._visit_all_code_lines_of(kernel, post_process='flatten')
            all_writes.extend(writes)

        return list(all_writes)

    @AstVisitor.accept("Assignment_Stmt")
    def _visit_assignment_stmt(self, node, context) -> list[Variable]:
        lhs_node, _, _ = node.children
        
        var_name = None

        if FparserTree(lhs_node).is_type("Name"):
            var_name = str(lhs_node)
        elif FparserTree(lhs_node).is_type("Part_Ref"):
            name_ast, _ = lhs_node.children
            var_name = str(name_ast)
        else:
            raise Exception(f"Unexpected LHS type in assignment statement: {FparserTree(lhs_node).tree.__class__.__name__}")

        write_var = context.get_variable_by_name(var_name)
        return [write_var]
