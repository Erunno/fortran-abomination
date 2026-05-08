from compiler.context import Variable
from compiler.cuda_generation.code_parts.cpp_types_gen import CppTyper
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.expression_walking.used_var import UsedVarsFinder
from compiler.kernel_abstraction import Kernel

class HostParamsGenerator:
    def __init__(self, kernels: list[Kernel]):
        self.kernels = kernels
        self.cpp_typer = CppTyper()
        self.variable_namer = VariableNamer()

    def generate_host_params(self) -> str:
        used_vars = set()
        used_vars_finder = UsedVarsFinder()
        
        for kernel in self.kernels:
            used_vars.update(used_vars_finder.find_used_vars(kernel))

        inout_vars = [var for var in used_vars if var.is_function_param()]
        return ",\n".join([self._get_host_param_code_for(var) for var in inout_vars])
    
    def _get_host_param_code_for(self, var: Variable) -> str:
        cpp_type_str = self.cpp_typer.get_cpp_type_str(var.type())
        dim = var.type().get_dim_count()

        var_decl = f"{cpp_type_str} {self.variable_namer.format_name(var)}"

        if dim == 0:
            return var_decl    
        
        size_t = self.cpp_typer.get_size_t()

        dim_vars_decls = ", ".join([
            f"{size_t} {self.variable_namer.format_array_dim_size_variable_name(var, d)}"
            for d in range(dim)])
        
        return f"{var_decl}, {dim_vars_decls}"
        