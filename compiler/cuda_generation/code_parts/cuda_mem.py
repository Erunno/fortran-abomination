from compiler.context import Variable
from compiler.cuda_generation.code_parts.cpp_types_gen import CppTyper
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.expression_walking.used_var import UsedVarsFinder
from compiler.kernel_abstraction import Kernel


class CudaMemCodeGenerator:
    def __init__(self, kernels: list[Kernel]):
        self.kernels = kernels
        self.all_used_arrays = self._get_all_used_arrays(self.kernels)
        self.var_namer = VariableNamer()
        self.typer = CppTyper()

    def generate_cuda_alloc_code(self) -> tuple[str, str]:
        def generate_cuda_malloc_for(var: Variable) -> str:
            type_name = self.typer.get_cpp_type_str(var.type())
            array_name_device = self.var_namer.format_device_name(var)

            total_bytes_expr = self._get_total_byte_count_of(var)

            var_declaration = f"{type_name} {array_name_device};"
            malloc_call = f"cudaMalloc(&{array_name_device}, {total_bytes_expr});"
            return (var_declaration, malloc_call)

        used_buffers = [generate_cuda_malloc_for(v) for v in self.all_used_arrays]

        device_buff_decls = '\n'.join([buf[0] for buf in used_buffers])
        cuda_allocation = '\n'.join([buf[1] for buf in used_buffers])

        return device_buff_decls, cuda_allocation

    def generate_cuda_dealloc_code(self) -> str:
        def generate_cuda_free_for(var: Variable) -> str:
            array_name_device = self.var_namer.format_device_name(var)
            return f"cudaFree({array_name_device});"

        return '\n'.join([generate_cuda_free_for(v) for v in self.all_used_arrays])

    def generate_cuda_host_to_device_copy_code(self) -> str:
        def generate_cuda_h2d_copy_for(var: Variable) -> str:
            array_name_device = self.var_namer.format_device_name(var)
            array_name_host = self.var_namer.format_name(var)

            total_bytes_expr = self._get_total_byte_count_of(var)

            return f"cudaMemcpy({array_name_device}, {array_name_host}, {total_bytes_expr}, cudaMemcpyHostToDevice);"

        return '\n'.join([generate_cuda_h2d_copy_for(v) for v in self.all_used_arrays])
    
    def generate_cuda_device_to_host_copy_code(self) -> str:
        def generate_cuda_d2h_copy_for(var: Variable) -> str:
            array_name_device = self.var_namer.format_device_name(var)
            array_name_host = self.var_namer.format_name(var)

            total_bytes_expr = self._get_total_byte_count_of(var)

            return f"cudaMemcpy({array_name_host}, {array_name_device}, {total_bytes_expr}, cudaMemcpyDeviceToHost);"

        params_vars = [v for v in self.all_used_arrays if v.is_function_param()]
        output_vars = [v for v in params_vars if v.is_output()]

        return '\n'.join([generate_cuda_d2h_copy_for(v) for v in output_vars])

    def generate_total_h2d_size_calculation(self) -> str:
        total_size_exprs = [self._get_total_byte_count_of(v) for v in self.all_used_arrays]
        total_size_expr = " + ".join(total_size_exprs)
        return total_size_expr
    
    def generate_total_d2h_size_calculation(self) -> str:
        params_vars = [v for v in self.all_used_arrays if v.is_function_param()]
        output_vars = [v for v in params_vars if v.is_output()]

        total_size_exprs = [self._get_total_byte_count_of(v) for v in output_vars]
        total_size_expr = " + ".join(total_size_exprs)
        return total_size_expr

    def _get_all_used_arrays(self, kernels: list[Kernel]) -> list[Variable]:
        finder = UsedVarsFinder()
        used_vars: set[Variable] = set()

        for kernel in kernels:
            used_vars.update(finder.find_used_vars(kernel))
        
        used_arrays = [v for v in used_vars if v.type().is_array()]
        return list(used_arrays)
    
    def _get_total_byte_count_of(self, var: Variable) -> str:
        sizes_vars = [self.var_namer.format_array_dim_size_variable_name(var, dim_num) 
                      for dim_num in range(var.type().get_dim_count())]

        total_size_expr = " * ".join(sizes_vars)
        total_bytes_expr = f'({self.typer.size_of(var.type().get_underlying_type())} * {total_size_expr})'
        return total_bytes_expr