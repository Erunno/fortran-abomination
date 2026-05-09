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