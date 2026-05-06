from compiler.context import Variable
from compiler.expression_walking.visitor_base import AstVisitor
from compiler.kernel_abstraction import Kernel

class UsedVarsFinder(AstVisitor):
    def find_all_used_vars(self, kernel: Kernel) -> list[Variable]:
        used_vars = [var 
                     for line, context in kernel.enum_lines_with_context()
                     for var in self._visit(line, context)
                    ]

        return list(set(used_vars))

    @AstVisitor.default_visit()
    def _visit_default(self, node, context) -> list[Variable]:
        if not hasattr(node, "children"):
            return []
        
        return [var for child in node.children for var in self._visit(child, context)]

    @AstVisitor.accept("name")
    def _visit_name(self, node, context) -> list[Variable]:
        var_name = str(node)
        return [context.get_variable_by_name(var_name)]
