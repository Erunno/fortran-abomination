from pathlib import Path

from compiler.context import Context
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator, CppForLoopGenerator
from compiler.cuda_generation.code_parts.cpp_types_gen import CppTyper
from compiler.cuda_generation.code_parts.do_loops import DoLoopGenerator
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.cuda_generation.kernel_depence import DependenceResolver, KernelGroup
from compiler.cuda_generation.templates.template import Template
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

        return self.cuda_call_template.code

    def generate_cuda_kernel_code(self) -> str:
        return "<Here goes the generated code for the CUDA kernel id: " + str(self.group_id) + ">"

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
    