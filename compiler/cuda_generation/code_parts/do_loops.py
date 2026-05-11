from compiler.context import DoLoopContext
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator


class DoLoopGenerator:
    def __init__(self):
        self.cpp_expr_gen = CppExprCodeGenerator()

    def generate_total_thread_count_expr(self, do_loop_contexts: list[DoLoopContext]) -> str:
        thread_count_exprs = [self._generate_thread_count_expr_for_context(ctx) for ctx in do_loop_contexts]
        return "(" + " * ".join(thread_count_exprs) + ")"
    
    def _generate_thread_count_expr_for_context(self, ctx: DoLoopContext) -> str:
        from_ast, to_ast, step_ast = ctx.range_code_ast_s()        

        from_code = self.cpp_expr_gen._visit(from_ast, ctx)
        to_code = self.cpp_expr_gen._visit(to_ast, ctx)
        
        count_code = f"({to_code} - {from_code} + 1)" # +1 because Fortran do loops are inclusive

        if step_ast is not None:
            step_code = self.cpp_expr_gen._visit(step_ast, ctx)
            count_code = f"({count_code} / {step_code})"

        return count_code
    

    def generate_for_loop(self, ctx: DoLoopContext) -> str:
        from_ast, to_ast, step_ast = ctx.range_code_ast_s()
        iter_var = ctx.get_iteration_variable()

        from_code = self.cpp_expr_gen._visit(from_ast, ctx)
        to_code = self.cpp_expr_gen._visit(to_ast, ctx)
        step_code = self.cpp_expr_gen._visit(step_ast, ctx) if step_ast is not None else None

        # Adjusting for 0-based indexing in C++
        from_code = f"({from_code}) - 1"
        to_code = f"({to_code}) - 1"

        if step_code is not None:
            loop_code = f"for (int {iter_var.name().lower()} = {from_code}; {iter_var.name().lower()} <= {to_code}; {iter_var.name().lower()} += {step_code}) {{\n"
        else:
            loop_code = f"for (int {iter_var.name().lower()} = {from_code}; {iter_var.name().lower()} <= {to_code}; {iter_var.name().lower()}++) {{\n"

        return loop_code
    
    def get_for_loop_closing(self) -> str:
        return "}\n"