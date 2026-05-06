from fparser.two.parser import ParserFactory
from fparser.common.readfortran import FortranFileReader
from pathlib import Path

from compiler.expression_walking.used_var import UsedSizesFinder, UsedVarsFinder
from compiler.kernel_abstraction import KernelFunctionDefinition
from compiler.kernels_finder import KernelFinder, SourceFilesCollection_FromFilesystem

from .fparser_tree_abstraction import FparserTree

def main() -> None:
    source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "gol_module.f90"

    file_collector = SourceFilesCollection_FromFilesystem().load_file(str(source_file))
    kernel_finder = KernelFinder(file_collector)

    kernel_functions = kernel_finder.load_all_kernels()
    gol: KernelFunctionDefinition = kernel_functions["second_gol_kernel"]

    for var in gol.local_context.variables:
        print(str(var))

    print (gol.name())

    kernels = gol.extract_kernels_graph()

    for kernel in kernels:
        print(str(kernel))

    print ("done parsing and extracting kernels\n\n")

    used_vars_finder = UsedVarsFinder()
    used_vars = used_vars_finder.find_all_used_vars(kernels[0])

    print("Used variables in the first kernel:")
    for var in used_vars:
        print(str(var))

    used_sizes_finder = UsedSizesFinder()
    used_sizes = used_sizes_finder.find_all_used_sizes(kernels[0])
    print("\nUsed sizes in the first kernel:")
    for var, arg_num in used_sizes:
        print(f"{var} (dimension index {arg_num})")


if __name__ == "__main__":
    main()