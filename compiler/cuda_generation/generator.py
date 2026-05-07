from compiler.kernel_abstraction import Kernel


class CudaGenerator:

    def generate_cuda_code(self: list[Kernel]) -> str:
        ...