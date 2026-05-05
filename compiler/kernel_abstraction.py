from compiler.context import Context, DoLoopContext, LocalContext
from compiler.fparser_tree_abstraction import FparserTree, LoopStatement

class Kernel:
    def __init__(self, context: Context):
        self.code_lines = []
        self.context = context

    def append_code_line(self, line_ast):
        self.code_lines.append(line_ast)

    def is_empty(self):
        return len(self.code_lines) == 0
    

    def __str__(self):
        code_str = "\n".join([str(line) for line in self.code_lines])
        tabbed_code_str = "\t" + code_str.replace("\n", "\n\t")

        context_str = str(self.context)
        tabbed_context_str = "\t" + context_str.replace("\n", "\n\t")

        return f"Kernel(\n  context=\n{tabbed_context_str},\n  code_lines=\n{tabbed_code_str}\n)"

class KernelFunctionDefinition:
    def __init__(self, kernel_ast):
        self.full_tree = FparserTree(kernel_ast)
        
        self.declaration_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Subroutine_Stmt")[0])
        self.specification_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Specification_Part")[0])
        self.code_ast = FparserTree(self.full_tree.get_all_nodes_in_children_of_type("Execution_Part")[0])

        self.local_context = LocalContext(self.specification_ast)

    def name(self):
        return str(self.declaration_ast.get_all_nodes_in_children_of_type("Name")[0])
   
    def extract_kernels_graph(self) -> list[Kernel]:
        return self._extract_kernels_sub_graph(self.code_ast.tree, self.local_context)
        
    def _extract_kernels_sub_graph(self, code_ast, current_context) -> list[Kernel]:

        class CurrentKernels:
            def __init__(self):
                self.kernels = []
                self.current_sub_kernel = Kernel(current_context)

            def add_code_line(self, line_ast):
                self.current_sub_kernel.append_code_line(line_ast)

            def finish_current_sub_kernel(self):
                if not self.current_sub_kernel.is_empty():
                    self.kernels.append(self.current_sub_kernel)
                    self.current_sub_kernel = Kernel(current_context)

        current_kernels = CurrentKernels()
        lines_of_code = FparserTree(code_ast).children_as_fTrees()

        for line in lines_of_code:
            if line.is_comment():
                continue

            if line.is_loop_definition():
                current_kernels.finish_current_sub_kernel()

                loop_statement = LoopStatement(line.tree)
                loop_context = DoLoopContext(loop_statement, current_context)

                execution_part = loop_statement.get_execution_part()

                sub_kernels = self._extract_kernels_sub_graph(execution_part, loop_context)  
                current_kernels.kernels.extend(sub_kernels)

            else:
                current_kernels.add_code_line(line.tree)

        current_kernels.finish_current_sub_kernel()
        return current_kernels.kernels

