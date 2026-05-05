from fparser.two.parser import ParserFactory
from fparser.common.readfortran import FortranFileReader
from pathlib import Path

from compiler.kernel_abstraction import KernelFunctionDefinition
from compiler.kernels_finder import KernelFinder, SourceFilesCollection_FromFilesystem

from .fparser_tree_abstraction import FparserTree

def main() -> None:
    source_file = Path(__file__).resolve().parents[1] / "fortran-stencils" / "gol_module.f90"

    file_collector = SourceFilesCollection_FromFilesystem().load_file(str(source_file))
    kernel_finder = KernelFinder(file_collector)

    kernel_functions = kernel_finder.load_all_kernels()
    gol: KernelFunctionDefinition = kernel_functions["gol_kernel"]

    for var in gol.local_context.variables:
        print(str(var))

    print (gol.name())

    kernels = gol.extract_kernels_graph()

    for kernel in kernels:
        print(str(kernel))
    
if __name__ == "__main__":
    main()