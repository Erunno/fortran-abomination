from itertools import groupby

from compiler.context import DoLoopContext
from compiler.kernel_abstraction import Kernel


class KernelGroup:
    def __init__(self, kernels, shared_outer_loop_contexts: list[DoLoopContext]):
        if len(kernels) == 0:
            raise Exception("Cannot create a KernelGroup with no kernels")
        self.kernels = kernels
        self.shared_outer_loop_contexts = shared_outer_loop_contexts

    def get_shared_outer_loop_contexts(self) -> list[DoLoopContext]:
        return self.shared_outer_loop_contexts

class DependenceResolver:
    def group_kernels(self, kernels: list[Kernel]) -> list[KernelGroup]:
        loop_contexts_from_outer_to_inner = [
            kernel_context.get_all_do_loop_contexts_from_outer_to_inner()
            for kernel_context in kernels
        ]
        return self._group_kernels_by_shared_do_loop_contexts(kernels, loop_contexts_from_outer_to_inner, [])
    
    def _group_kernels_by_shared_do_loop_contexts(self, kernels, kernels_do_loop_contexts, shared_contexts_so_far = []):
        if any(len(contexts) == 0 for contexts in kernels_do_loop_contexts):
            return [KernelGroup(kernels, shared_contexts_so_far)]
         
        def get_first_do_loop_context(kernel_and_contexts):
            _, contexts_of_kernel = kernel_and_contexts
            return contexts_of_kernel[0] if contexts_of_kernel else None

        zipped_data = list(zip(kernels, kernels_do_loop_contexts))
        sub_groups = groupby(zipped_data, get_first_do_loop_context)
        
        result_groups = []

        for do_loop_context, group in sub_groups:
            group = list(group)
            kernels_in_group = [kernel for kernel, _ in group]
            new_contexts = [contexts[1:] for _, contexts in group]
            new_shared_contexts = shared_contexts_so_far + [do_loop_context] 

            sub_groups = self._group_kernels_by_shared_do_loop_contexts(kernels_in_group, new_contexts, new_shared_contexts)
            result_groups.extend(sub_groups)

        return result_groups
