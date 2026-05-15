from compiler.context import Variable
from compiler.cuda_generation.code_parts.cpp_types_gen import FortranTyper
from compiler.cuda_generation.code_parts.host_params import ParamsGenerator
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.expression_walking.used_var import UsedVarsFinder
from compiler.kernel_abstraction import KernelFunctionDefinition


class FortranInterfaceGenerator:
    def __init__(self, kernels: list[KernelFunctionDefinition], entry_kernel_func: KernelFunctionDefinition):
        self.kernels = kernels
        self.entry_kernel_func = entry_kernel_func

        self.variable_namer = VariableNamer()
        self.fortran_typer = FortranTyper(self.variable_namer)

    def generate_interface_dummies(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        fortran_params = [self._get_fortran_params_from(var) for var in inout_vars]
        
        dummy_lines = [', '.join([param.name for param in params]) for params in fortran_params]
        return ', &\n'.join(dummy_lines)

    def generate_interface_decls(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        fortran_params = [self._get_fortran_params_from(var) for var in inout_vars]

        decl_lines = [
            f"{param.type_str} :: {param.name}"
            for params in fortran_params for param in params
        ]
        
        return '\n'.join(decl_lines)
    
    def generate_cpp_kernel_call(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        fortran_params = [self._get_fortran_params_from(var) for var in inout_vars]

        dummy_lines = [', '.join([param.casted_to_cpp for param in params]) for params in fortran_params]
        return ', &\n'.join(dummy_lines)

    def generate_original_func_args_dummies(self) -> str:
        original_func_params = self.entry_kernel_func.parameters()
        dummy_lines = [self.variable_namer.format_name(param) for param in original_func_params]
        return ', &\n'.join(dummy_lines)
    
    def generate_original_func_args_decls(self) -> str:
        params = self.entry_kernel_func.parameters()
        decl_lines = [
            f"{self.fortran_typer.get_fortran_type_decl(param)} :: {self.variable_namer.format_name(param)}"
            for param in params]
        return '\n'.join(decl_lines)

    class FortranParamInfo:
        def __init__(self, type_str: str, name: str, casted_to_cpp: str):
            self.type_str = type_str
            self.name = name
            self.casted_to_cpp = casted_to_cpp

    def _get_fortran_params_from(self, var: Variable) -> list["ParamsGenerator.FortranParamInfo"]:
        fortran_type_str = self.fortran_typer.get_fortran_type_for_cpp_bind(var.type())
        var_name = self.variable_namer.format_name(var)
        dim_count = var.type().get_dim_count()

        params = [self.FortranParamInfo(
            fortran_type_str, var_name,
            self.fortran_typer.cast_to_cpp_bind(var))]

        size_t = self.fortran_typer.get_size_t_cpp_bind()
        dim_size_infos = []
        for dim_num in range(dim_count):
            size_var_name = self.variable_namer.format_array_dim_size_variable_name(var, dim_num)
            dim_size_infos.append(self.FortranParamInfo(
                size_t, size_var_name,
                self.fortran_typer.casted_size(var, dim_num)))

        return params + dim_size_infos