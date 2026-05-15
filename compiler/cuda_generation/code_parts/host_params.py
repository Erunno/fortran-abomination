from compiler.context import DoLoopContext, IterationVariable, Variable
from compiler.cuda_generation.code_parts.cpp_types_gen import CppTyper, FortranTyper
from compiler.cuda_generation.code_parts.variable_namer import VariableNamer
from compiler.expression_walking.used_var import UsedVarsFinder, WriteVarsFinder
from compiler.kernel_abstraction import Kernel

class ParamsGenerator:
    def __init__(self, kernels: list[Kernel], preceding_kernels: list[Kernel]):
        self.kernels = kernels
        self.preceding_kernels = preceding_kernels
        self.write_vars_finder = WriteVarsFinder()
        self.cpp_typer = CppTyper()
        self.fortran_typer = FortranTyper()
        self.variable_namer = VariableNamer()

    def generate_host_params(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        return ", &\n".join([self._get_cpp_param_code_for(var) for var in inout_vars])
    
    def generate_fortran_interface_dummies(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        fortran_params = [self._get_fortran_params_from(var) for var in inout_vars]
        
        dummy_lines = [', '.join([param.name for param in params]) for params in fortran_params]
        return ', &\n'.join(dummy_lines)

    def generate_fortran_interface_decls(self) -> str:
        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        inout_vars = [var for var in used_vars if var.is_function_param()]
        fortran_params = [self._get_fortran_params_from(var) for var in inout_vars]

        decl_lines = []
        for params in fortran_params:
            for param in params:
                decl_lines.append(f"{param.type_str} :: {param.name}")
        
        return '\n'.join(decl_lines)

    def generate_device_params_decl(self, outer_iter_space: list[DoLoopContext]) -> str:
        para_vars = self.get_device_params_variables()
        params_decl = ",\n".join([self._get_device_param_decl(var) for var in para_vars])

        if len(outer_iter_space) == 0:
            return params_decl
        
        iter_space_params = self._generate_iter_space_params(outer_iter_space)
        iter_space_params_decl = ",\n".join([", ".join([type_str + " " + name for type_str, name in part]) for part in iter_space_params])

        return f"{params_decl},\n{iter_space_params_decl}"

    def generate_device_param_call(self, outer_iter_space: list[DoLoopContext]) -> str:
        para_vars = self.get_device_params_variables()
        params_call = ",\n".join([self._get_device_param_call_arg(var) for var in para_vars])

        if len(outer_iter_space) == 0:
            return params_call

        iter_space_params = self._generate_iter_space_params(outer_iter_space)
        parts_without_types = [
            [name for type_str, name in part] for part in iter_space_params
        ]

        iter_space_params_call = ",\n".join([", ".join(part) for part in parts_without_types])

        return f"{params_call},\n{iter_space_params_call}"
    
    def _generate_iter_space_params(self, outer_iter_space: list[DoLoopContext]) -> list[list[tuple[str, str]]]:
        iter_vars = [ctx.get_iteration_variable() for ctx in outer_iter_space]
        def get_part_for(iter_var: IterationVariable) -> str:
            iter_var_names = self.variable_namer.format_iter_var_names(iter_var)

            parts = [iter_var_names.from_name, iter_var_names.to_name, iter_var_names.step_name]

            _, _, step_ast = iter_var.loop_statement.range_code_ast_s()
            if step_ast is None:
                parts.remove(iter_var_names.step_name)

            type_str = self.cpp_typer.get_cpp_type_str(iter_var.type())

            return [(type_str, name) for name in parts]

        return [get_part_for(iter_var) for iter_var in iter_vars]

    def _get_iter_space_(self, outer_iter_space: list[DoLoopContext]) -> list[Variable]:
        iter_space_vars = []
        for ctx in outer_iter_space:
            from_var = ctx.range_code_ast_s()[0]
            to_var = ctx.range_code_ast_s()[1]
            step_var = ctx.range_code_ast_s()[2]

            iter_space_vars.extend([from_var, to_var])
            if step_var is not None:
                iter_space_vars.append(step_var)
        
        return iter_space_vars

    def _get_device_param_decl(self, var: Variable) -> str:
        cpp_type_str = self.cpp_typer.get_cpp_type_str(var.type())
        array_name_device = self.variable_namer.format_name(var)

        if not var.type().is_array():
            return f"{cpp_type_str} {array_name_device}"

        sizes_str = self._get_sizes_param_code_for(var)

        return f"{cpp_type_str} {array_name_device}, {sizes_str}"


    def _get_device_param_call_arg(self, var: Variable) -> str:
        var_name = self.variable_namer.format_device_name(var)

        if not var.type().is_array():
            return var_name

        sizes = [self.variable_namer.format_array_dim_size_variable_name(var, d)
                 for d in range(var.type().get_dim_count())]
        
        return f"{var_name}, {', '.join(sizes)}"
    
    def get_device_params_variables(self) -> list[Variable]:
        variables_written_to_by_preceding_kernels = self.write_vars_finder.find_variables_written_to(self.preceding_kernels)

        used_vars = UsedVarsFinder().find_used_vars(self.kernels)
        used_vars = [var for var in used_vars if var.is_function_param() or var in variables_written_to_by_preceding_kernels]
        used_vars.sort(key=lambda v: v.name())

        return list(set(used_vars))

    def _get_cpp_param_code_for(self, var: Variable) -> str:
        cpp_type_str = self.cpp_typer.get_cpp_type_str(var.type())
        dim = var.type().get_dim_count()

        var_decl = f"{cpp_type_str} {self.variable_namer.format_name(var)}"

        if dim == 0:
            return var_decl    
        
        dim_vars_decls = self._get_sizes_param_code_for(var)
        
        return f"{var_decl}, {dim_vars_decls}"
    
    class FortranParamInfo:
        def __init__(self, type_str: str, name: str):
            self.type_str = type_str
            self.name = name

    def _get_fortran_params_from(self, var: Variable) -> list["ParamsGenerator.FortranParamInfo"]:
        fortran_type_str = self.fortran_typer.get_fortran_type_for_cpp_bind(var.type())
        var_name = self.variable_namer.format_name(var)
        dim_count = var.type().get_dim_count()

        params = [self.FortranParamInfo(fortran_type_str, var_name)]

        size_t = self.fortran_typer.get_size_t_cpp_bind()
        dim_size_infos = []
        for dim_num in range(dim_count):
            size_var_name = self.variable_namer.format_array_dim_size_variable_name(var, dim_num)
            dim_size_infos.append(self.FortranParamInfo(size_t, size_var_name))

        return params + dim_size_infos


    def _get_sizes_param_code_for(self, var: Variable) -> str:
        size_t = self.cpp_typer.get_size_t()
        dim = var.type().get_dim_count()

        dim_vars_decls = ", ".join([
            f"{size_t} {self.variable_namer.format_array_dim_size_variable_name(var, d)}"
            for d in range(dim)])
        
        return dim_vars_decls
        