from fparser.two.parser import ParserFactory
from fparser.common.readfortran import FortranFileReader
from pathlib import Path

from compiler.cuda_generation.generator import FullCodeGenerator
from compiler.cuda_generation.kernel_depence import DependenceResolver
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator
from compiler.expression_walking.used_var import UsedSizesFinder, UsedVarsFinder
from compiler.kernel_abstraction import KernelFunctionDefinition
from compiler.kernels_finder import KernelFinder, SourceFilesCollection_FromFilesystem

from .fparser_tree_abstraction import FparserTree

def main() -> None:
    # source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "gol_module.f90"
    # source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "elmm_cdv.f90"
    # source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "elmm_cdw.f90"
    source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "elmm_cdu.f90"

    file_collector = SourceFilesCollection_FromFilesystem().load_file(str(source_file))
    kernel_finder = KernelFinder(file_collector)

    kernel_functions = kernel_finder.load_all_kernels()
    gol: KernelFunctionDefinition = kernel_functions["CDU"]

    for var in gol.local_context.variables:
        print(str(var))

    print (gol.name())

    kernels = gol.extract_kernels_graph()
    func_name = gol.name()

    for kernel in kernels:
        print(str(kernel))

        print (f"\n===== Do Loop Contexts in this kernel ({len(list(kernel.get_all_do_loop_contexts_from_outer_to_inner()))}) =====\n")
        print(*[str(do_loop_context) for do_loop_context in kernel.get_all_do_loop_contexts_from_outer_to_inner()], sep="\n")
        print("\n===== End Do Loop Contexts =====\n\n\n")

    print ("done parsing and extracting kernels\n\n")

    used_vars_finder = UsedVarsFinder()
    used_vars = used_vars_finder.find_used_vars(kernels[0])

    print("Used variables in the first kernel:")
    for var in used_vars:
        print(str(var))

    used_sizes_finder = UsedSizesFinder()
    used_sizes = used_sizes_finder.find_all_used_sizes(kernels[0])
    print("\nUsed sizes in the first kernel:")
    for var, arg_num in used_sizes:
        print(f"{var} (dimension index {arg_num})")

    print ("\nGrouping kernels by shared loop contexts...\n")
    
    dependence_resolver = DependenceResolver()
    kernel_groups = dependence_resolver.group_kernels(kernels)
    print(f"\nKernel groups (total {len(kernel_groups)} groups):")
    for i, group in enumerate(kernel_groups):
        print(f"\nGroup {i+1} (total {len(group.kernels)} kernels):")
        print(f"Shared outer loop contexts for this group:")
        for context in group.get_shared_outer_loop_contexts():
            print(str(context))
        
        for kernel in group.kernels:
            print(str(kernel))


    gen = CppExprCodeGenerator()
    generates_lines = gen.generate_cpp_code(kernels[0])
    print("\nGenerated C++ code for the first kernel:")
    print(generates_lines)

    print("code generation:")
    full_code_gen = FullCodeGenerator(kernels, gol)
    code = full_code_gen.generate_cuda_code()
    print(f"Generated CUDA code:\n{code}")

    fortran_interface_code = full_code_gen.generate_fortran_interface_code()
    print(f"Generated Fortran interface code:\n{fortran_interface_code}")

    code_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "generated_code.cu"
    with open(code_file, "w") as f:
        f.write(code)

    fotran_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "generated_interface.f90"
    with open(fotran_file, "w") as f:
        f.write(fortran_interface_code)

if __name__ == "__main__":
    main()