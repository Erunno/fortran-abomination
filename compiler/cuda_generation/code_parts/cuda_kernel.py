from pathlib import Path

from compiler.context import Context, DoLoopContext
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator
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
        self.do_generator = DoLoopGenerator()
        self.typer = CppTyper()
        self.used_vars_finder = UsedVarsFinder()
        self.param_gen = ParamsGenerator(group.kernels)

        cuda_ker_template_path = Path(__file__).resolve().parent.parent / "templates" / "single_cuda_kernel_template.cu"
        self.cuda_code_kernel_template = Template(str(cuda_ker_template_path))

        cuda_call_template_path = Path(__file__).resolve().parent.parent / "templates" / "cuda_call_template.cu"
        self.cuda_call_template = Template(str(cuda_call_template_path))
        self.tab = Template.tab

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
            step_code = self.expr_code_generator.generate_cpp_code_for_ast(step_ast, ctx) if step_ast is not None else None

            from_code = f'({from_code}) - 1'
            to_code = f'({to_code}) - 1'

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

        indexing_calculations_code = self._get_outer_space_index_calculation_code()
        self.cuda_code_kernel_template.replace_placeholder("INDEX_MAPPING_LOGIC", indexing_calculations_code, tabs=1)

        body_code = self._generate_kernel_body_code()
        self.cuda_code_kernel_template.replace_placeholder("KERNEL_BODY", body_code, tabs=1)

        return self.cuda_code_kernel_template.code

    def _generate_kernel_body_code(self) -> str:

        def _tab_code(code: str) -> str:
            return "\n".join([
                self.tab + line if line.strip() else line
                for line in code.split("\n")])
        
        def _generate_body_for_kernel(kernels: list[Kernel], loop_depth: int) -> tuple[str, list[Kernel]]:
            if len(kernels) == 0:
                return "", []

            first_kernel, *rest_kernels = kernels
            kernel_loop_depth = first_kernel.get_loop_depth()

            if kernel_loop_depth > loop_depth:
                first_unaddressed_loop_ctx = first_kernel.get_all_do_loop_contexts_from_outer_to_inner()[loop_depth]

                loop_start = self.do_generator.generate_for_loop(first_unaddressed_loop_ctx)
                code, rest_of_kernels = _generate_body_for_kernel(kernels, loop_depth + 1)
                loop_end = self.do_generator.get_for_loop_closing()
                
                full_code = loop_start + _tab_code(code) + loop_end
                return full_code, rest_of_kernels

            kernel_code = self.expr_code_generator.generate_cpp_code(first_kernel)
            rest_code, rest_of_kernels = _generate_body_for_kernel(rest_kernels, loop_depth)

            full_code = kernel_code + "\n" + rest_code

            return full_code, rest_of_kernels

        kernels = self.group.kernels
        full_code = ""
        outer_loop_depth = len(self.group.get_shared_outer_loop_contexts())

        while len(kernels) > 0:
            code, kernels = _generate_body_for_kernel(kernels, outer_loop_depth)
            full_code += code + "\n"

        return full_code

    def _get_outer_space_index_calculation_code(self) -> str:
        missing_steps_vars = [
            ctx.get_iteration_variable()
            for ctx in self.group.get_shared_outer_loop_contexts()
            if ctx.range_code_ast_s()[2] is None
        ]

        decl_constexpr_step_vars = "\n    ".join([
            f"constexpr {self.typer.get_cpp_type_str(iter_var.type())} {self.variable_namer.format_iter_var_names(iter_var).step_name} = 1;"
            for iter_var in missing_steps_vars
        ])
        
        all_indexing_vars = [ctx.get_iteration_variable() for ctx in self.group.get_shared_outer_loop_contexts()]
        indexing_vars_names = [self.variable_namer.format_iter_var_names(var) for var in all_indexing_vars]

        # Adjusted for safe ceiling division assuming inclusive 'to' boundaries:
        # Number of iterations = (distance + step) / step
        def get_count_in_dim(var_names) -> str:
            return f"(({var_names.to_name} - {var_names.from_name} + {var_names.step_name}) / {var_names.step_name})"

        code_lines = []
        
        if decl_constexpr_step_vars:
            code_lines.append(decl_constexpr_step_vars)
            
        size_t = self.typer.get_size_t() 

        # Initialize the working index
        code_lines.append(f"{size_t} current_idx = idx;")
        
        # Unroll the dimension calculations into C++
        for i, var in enumerate(indexing_vars_names):
            num_dim_var = f"num_{var.name}"
            local_dim_var = f"local_{var.name}"
            
            code_lines.append(f"\n// Calculate index for '{var.name}' dimension")
            code_lines.append(f"{size_t} {num_dim_var} = {get_count_in_dim(var)};")
            
            # For all dimensions EXCEPT the last one, use modulo and division
            if i < len(indexing_vars_names) - 1:
                code_lines.append(f"{size_t} {local_dim_var} = current_idx % {num_dim_var};")
                code_lines.append(f"{var.type} {var.name} = {var.from_name} + {local_dim_var} * {var.step_name};")
                code_lines.append(f"current_idx /= {num_dim_var};")
            else:
                # OPTIMIZATION: The last (slowest) dimension doesn't need modulo or division.
                # current_idx inherently contains only the remainder for this final dimension.
                code_lines.append(f"{size_t} {local_dim_var} = current_idx;")
                code_lines.append(f"{var.type} {var.name} = {var.from_name} + {local_dim_var} * {var.step_name};")

        return "\n".join(code_lines)


class CudaKernelGenerator:
    def __init__(self, kernels: list[Kernel]):
        self.kernels = kernels
        self.variable_namer = VariableNamer()
        self.typer = CppTyper()
        self.expr_code_generator = CppExprCodeGenerator(self.variable_namer)

        kernel_groups = DependenceResolver().group_kernels(kernels)
        self.kernel_group_generators = [KernelGroupGenerator(group, group_id) 
                                        for group_id, group in enumerate(kernel_groups)] 

    def generate_cuda_kernel_calls(self) -> str:
        return "\n".join([group_gen.generate_cuda_kernel_call() for group_gen in self.kernel_group_generators])

    def generate_cuda_kernels_code(self) -> str:
        return "\n".join([group_gen.generate_cuda_kernel_code() for group_gen in self.kernel_group_generators])
    