from pathlib import Path
import re

from compiler.cuda_generation.code_parts.cuda_mem import CudaMemCodeGenerator
from compiler.cuda_generation.code_parts.host_params import HostParamsGenerator
from compiler.cuda_generation.code_parts.kernel_func_namer import KernelFuncNamer
from compiler.kernel_abstraction import Kernel


class Template:
    def __init__(self, file_path):
        self.code_path = file_path
        with open(file_path, 'r') as f:
            self.code = f.read() 

    def replace_placeholder(self, placeholder_name, replacement_code, tabs=0):
        tabs_str = "    " * tabs
        replacement_code = "\n".join([tabs_str + line for line in replacement_code.splitlines()])
        regex_pattern = r"[ \t]*\$" + re.escape(placeholder_name) + r"\$"
        self.code = re.sub(regex_pattern, replacement_code, self.code)

    def write_to_file(self, output_file_path):
        with open(output_file_path, 'w') as f:
            f.write(self.code)

    def print_code(self):
        print(self.code)

    def get_fresh_instance(self) -> "Template":
        return Template(self.code_path)
    
class FullCodeGenerator:
    def __init__(self, kernels: list[Kernel]):
        path_to_templates = Path(__file__).resolve().parent / "templates"

        self.cu_file_template = Template(path_to_templates / "kernels_interface_template.cu")
        self.cuda_call_template = Template(path_to_templates / "cuda_call_template.cu")
        self.cuda_kernel_template = Template(path_to_templates / "single_cuda_kernel_template.cu")

        self.host_params_generator = HostParamsGenerator(kernels)
        self.kernel_func_namer = KernelFuncNamer()
        self.cuda_mem_code_generator = CudaMemCodeGenerator(kernels)

    def generate_cuda_code(self) -> str:
        in_cpp_func_tabs = 2
        host_params = self.host_params_generator.generate_host_params()
        self.cu_file_template.replace_placeholder("HOST_PARAMETERS", host_params, tabs=in_cpp_func_tabs)

        cuda_allocation = self.cuda_mem_code_generator.generate_cuda_alloc_code()
        self.cu_file_template.replace_placeholder("MEMORY_ALLOCATIONS", cuda_allocation, tabs=in_cpp_func_tabs)

        cuda_H2D_copy = self.cuda_mem_code_generator.generate_cuda_host_to_device_copy_code()
        self.cu_file_template.replace_placeholder("CUDA_H2D_COPY", cuda_H2D_copy, tabs=in_cpp_func_tabs)

        cuda_D2H_copy = self.cuda_mem_code_generator.generate_cuda_device_to_host_copy_code()
        self.cu_file_template.replace_placeholder("CUDA_D2H_COPY", cuda_D2H_copy, tabs=in_cpp_func_tabs)

        cuda_deallocation = self.cuda_mem_code_generator.generate_cuda_dealloc_code()
        self.cu_file_template.replace_placeholder("MEMORY_FREES", cuda_deallocation, tabs=in_cpp_func_tabs)

        print(f"Generated host parameters:\n{host_params}")
        return self.cu_file_template.code
        
