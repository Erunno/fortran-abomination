from typing import List

from compiler.cuda_generation.code_parts.cuda_kernel import KernelGroupGenerator
from compiler.cuda_generation.kernel_depence import KernelGroup
from compiler.kernel_abstraction import Kernel


class PureCppGenerator():
    def __init__(self, kernels: List[Kernel]):
        self.kernels = kernels
        
        group_of_all = KernelGroup(kernels, shared_outer_loop_contexts=[])
        self.cpp_code_generator = KernelGroupGenerator(group_of_all, group_id="pure_cpp_impl")

    def generate_kernel_body(self):
        return self.cpp_code_generator.generate_kernel_body_code()

    def generate_local_var_decls(self):
        return self.cpp_code_generator.generate_decls_of_local_vars()
