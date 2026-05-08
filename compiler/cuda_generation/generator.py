from pathlib import Path

from compiler.cuda_generation.code_parts.host_params import HostParamsGenerator
from compiler.cuda_generation.code_parts.kernel_func_namer import KernelFuncNamer
from compiler.kernel_abstraction import Kernel


class Template:
    def __init__(self, file_path):
        self.code_path = file_path
        with open(file_path, 'r') as f:
            self.code = f.read() 

    def replace_placeholder(self, placeholder_name, replacement_code):
        self.code = self.code.replace(f"${placeholder_name}$", replacement_code)

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

    def generate_cuda_code(self) -> str:
        host_params = self.host_params_generator.generate_host_params()
        print(f"Generated host parameters:\n{host_params}")
        return "xxx"
        
