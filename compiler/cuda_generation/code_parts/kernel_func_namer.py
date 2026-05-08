class KernelFuncNamer:
    def __init__(self):
        self.kernel_count = 0

    def get_cpp_func_name(self) -> str:
        name = f"kernel_{self.kernel_count}"
        self.kernel_count += 1
        return name

    def get_cuda_global_func_name(self) -> str:
        return self.get_cpp_func_name()