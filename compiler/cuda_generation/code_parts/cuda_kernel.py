from pathlib import Path

from compiler.context import Context, DoLoopContext
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator, CppForLoopGenerator
from compiler.cuda_generation.code_parts.cpp_types_gen import CppTyper
from compiler.cuda_generation.code_parts.do_loops import DoLoopGenerator
from compiler.cuda_generation.code_parts.host_params import ParamsGenerator
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.cuda_generation.kernel_depence import DependenceResolver, KernelGroup
from compiler.cuda_generation.templates.template import Template
from compiler.expression_walking.used_var import UsedVarsFinder
from compiler.kernel_abstraction import Kernel

class KernelGroupGenerator:
    def __init__(self, group: KernelGroup, group_id: any):
        self.group = group
        self.group_id = group_id
        self.variable_namer = VariableNamer()
        self.typer = CppTyper()
        self.expr_code_generator = CppExprCodeGenerator(self.variable_namer)
        self.for_loop_generator = CppForLoopGenerator()
        self.do_generator = DoLoopGenerator()
        self.typer = CppTyper()
        self.used_vars_finder = UsedVarsFinder()
        self.param_gen = ParamsGenerator(group.kernels)

        cuda_ker_template_path = Path(__file__).resolve().parent.parent / "templates" / "single_cuda_kernel_template.cu"
        self.cuda_code_kernel_template = Template(str(cuda_ker_template_path))

        cuda_call_template_path = Path(__file__).resolve().parent.parent / "templates" / "cuda_call_template.cu"
        self.cuda_call_template = Template(str(cuda_call_template_path))

        self.cuda_kernel_name = f"kernel_group_{self.group_id}"
        self.block_size = 256


    def generate_cuda_kernel_call(self) -> str:
        self.cuda_call_template.replace_placeholder("KERNEL_ID", str(self.group_id))
        self.cuda_call_template.replace_placeholder("KERNEL_NAME", self.cuda_kernel_name, tabs=1)
        self.cuda_call_template.replace_placeholder("BLOCK_SIZE", str(self.block_size))

        thread_count_expr = self.do_generator.generate_total_thread_count_expr(self.group.shared_outer_loop_contexts)
        self.cuda_call_template.replace_placeholder("TOTAL_ELEMENTS", thread_count_expr)

        device_param_call_args = self.param_gen.generate_device_param_call(
            outer_iter_space=self.group.get_shared_outer_loop_contexts()
        )

        self.cuda_call_template.replace_placeholder("KERNEL_ARGS", device_param_call_args, tabs=2)

        ranges_calculations_code = self._generate_ranges_calculations_code()
        self.cuda_call_template.replace_placeholder("RANGES_CALCULATIONS", ranges_calculations_code, tabs=1)

        return self.cuda_call_template.code

    def _generate_ranges_calculations_code(self) -> str:
        def get_range_calculations_for(ctx: DoLoopContext) -> str:
            from_ast, to_ast, step_ast = ctx.range_code_ast_s()
            iter_var = ctx.get_iteration_variable()
            
            from_code = self.expr_code_generator.generate_cpp_code_for_ast(from_ast, ctx)
            to_code = self.expr_code_generator.generate_cpp_code_for_ast(to_ast, ctx)
            step_code = self.expr_code_generator.generate_cpp_code_for_ast(step_ast, ctx)

            iter_var_names = self.variable_namer.format_iter_var_names(iter_var)
            type_str = self.typer.get_cpp_type_str(iter_var.type())

            def get_line_for(name: str, code: str) -> str:
                return f"{type_str} {name} = {code};"
            
            result = get_line_for(iter_var_names.from_name, from_code) + "\n" + \
                     get_line_for(iter_var_names.to_name, to_code) + "\n"
            
            if step_ast is not None:
                result += get_line_for(iter_var_names.step_name, step_code) + "\n"

            return result

        range_calculations = [get_range_calculations_for(ctx) for ctx in self.group.get_shared_outer_loop_contexts()]
        return "\n".join(range_calculations)

    def generate_cuda_kernel_code(self) -> str:
        self.cuda_code_kernel_template.replace_placeholder("KERNEL_NAME", self.cuda_kernel_name)

        device_param_decls = self.param_gen.generate_device_params_decl(
            outer_iter_space=self.group.get_shared_outer_loop_contexts()
        )
        self.cuda_code_kernel_template.replace_placeholder("DEVICE_PARAMETERS", device_param_decls, tabs=1)

        return self.cuda_code_kernel_template.code

class CudaKernelGenerator:
    def __init__(self, kernels: list[Kernel]):
        self.kernels = kernels
        self.variable_namer = VariableNamer()
        self.typer = CppTyper()
        self.expr_code_generator = CppExprCodeGenerator(self.variable_namer)
        self.for_loop_generator = CppForLoopGenerator()

        kernel_groups = DependenceResolver().group_kernels(kernels)
        self.kernel_group_generators = [KernelGroupGenerator(group, group_id) 
                                        for group_id, group in enumerate(kernel_groups)] 

    def generate_cuda_kernel_calls(self) -> str:
        return "\n".join([group_gen.generate_cuda_kernel_call() for group_gen in self.kernel_group_generators])

    def generate_cuda_kernels_code(self) -> str:
        return "\n".join([group_gen.generate_cuda_kernel_code() for group_gen in self.kernel_group_generators])
    