from typing import List

from compiler.cuda_generation.code_parts.cuda_kernel import KernelGroupGenerator
from compiler.cuda_generation.kernel_depence import DependenceResolver, KernelGroup
from compiler.kernel_abstraction import Kernel


class PureCppGenerator():
    def __init__(self, kernels: List[Kernel]):
        self.kernels = kernels
        
        group_of_all = KernelGroup(kernels, shared_outer_loop_contexts=[])
        self.all_kernels_group_gen = KernelGroupGenerator(group_of_all, group_id="pure_cpp_impl")

        kernel_groups = DependenceResolver().group_kernels(kernels)
        self.kernel_group_generators = [KernelGroupGenerator(group, group_id) 
                                        for group_id, group in enumerate(kernel_groups)]

    def generate_kernel_body(self):
        return "".join([
            self._generate_one_loop_nest(gen)
            for gen in self.kernel_group_generators])

    def generate_local_var_decls(self):
        return self.all_kernels_group_gen.generate_decls_of_local_vars()

    def _generate_one_loop_nest(self, group_gen: KernelGroupGenerator) -> str:
        pragma = group_gen.generate_omp_pragma()
        code = group_gen.generate_kernel_body_code(ignore_shared_outer_loops=True)

        return pragma + code
