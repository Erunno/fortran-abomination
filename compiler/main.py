import argparse
import shutil
from pathlib import Path

from compiler.cuda_generation.generator import FullCodeGenerator
from compiler.cuda_generation.kernel_depence import DependenceResolver
from compiler.cuda_generation.code_parts.cpp_code_line_gen import CppExprCodeGenerator
from compiler.expression_walking.used_var import UsedSizesFinder, UsedVarsFinder
from compiler.kernel_abstraction import KernelFunctionDefinition
from compiler.kernels_finder import KernelFinder, SourceFilesCollection_FromFilesystem

_TEMPLATES_DIR = Path(__file__).resolve().parent / "cuda_generation" / "templates"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='python -m compiler',
        description='Generate CUDA / C++ / Fortran code from a Fortran stencil kernel.',
    )
    parser.add_argument(
        '--input', '-i', required=True, metavar='FILE',
        help='Input Fortran source file.',
    )
    parser.add_argument(
        '--kernel', '-k', required=True, metavar='NAME',
        help='Entry kernel function name (case-sensitive).',
    )
    parser.add_argument(
        '--output-dir', '-o', default='.', metavar='DIR',
        help='Directory for all generated output files (default: current directory).',
    )
    parser.add_argument(
        '--cuda-output', default='generated_code.cu', metavar='FILE',
        help='CUDA output filename (default: generated_code.cu).',
    )
    parser.add_argument(
        '--cpp-output', default='generated_cpp_impl.cpp', metavar='FILE',
        help='C++ implementation output filename (default: generated_cpp_impl.cpp).',
    )
    parser.add_argument(
        '--fortran-output', default='generated_interface.f90', metavar='FILE',
        help='Fortran interface output filename (default: generated_interface.f90).',
    )
    parser.add_argument(
        '--common-header', default='common_functions.cuh', metavar='FILE',
        help='Common functions header output filename (default: common_functions.cuh).',
    )
    parser.add_argument(
        '--no-common-header', action='store_true',
        help='Skip writing the common_functions.cuh header.',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print detailed parsing and generation information.',
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    source_file = Path(args.input).resolve()
    if not source_file.exists():
        raise SystemExit(f"error: input file not found: {source_file}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── parse & extract kernels ───────────────────────────────────────────────
    file_collector = SourceFilesCollection_FromFilesystem().load_file(str(source_file))
    kernel_finder = KernelFinder(file_collector)
    kernel_functions = kernel_finder.load_all_kernels()

    func = args.kernel
    if func not in kernel_functions:
        available = ', '.join(kernel_functions.keys())
        raise SystemExit(f"error: kernel '{func}' not found in {source_file}\n"
                         f"       available kernels: {available}")

    main_func: KernelFunctionDefinition = kernel_functions[func]
    kernels = main_func.extract_kernels_graph()

    # ── verbose debug output ──────────────────────────────────────────────────
    if args.verbose:
        print("Local context variables:")
        for var in main_func.local_context.variables:
            print(f"  {var}")
        print(f"\nKernel function: {main_func.name()}")

        for kernel in kernels:
            print(str(kernel))
            do_loop_contexts = list(kernel.get_all_do_loop_contexts_from_outer_to_inner())
            print(f"\n===== Do Loop Contexts ({len(do_loop_contexts)}) =====")
            print(*[str(ctx) for ctx in do_loop_contexts], sep="\n")
            print("===== End Do Loop Contexts =====\n")

        used_vars = UsedVarsFinder().find_used_vars(kernels[0])
        print("Used variables in the first kernel:")
        for var in used_vars:
            print(f"  {var}")

        used_sizes = UsedSizesFinder().find_all_used_sizes(kernels[0])
        print("\nUsed sizes in the first kernel:")
        for var, arg_num in used_sizes:
            print(f"  {var}  (dimension index {arg_num})")

        kernel_groups = DependenceResolver().group_kernels(kernels)
        print(f"\nKernel groups ({len(kernel_groups)} total):")
        for i, group in enumerate(kernel_groups):
            print(f"\n  Group {i + 1} ({len(group.kernels)} kernels):")
            for ctx in group.get_shared_outer_loop_contexts():
                print(f"    shared loop: {ctx}")
            for kernel in group.kernels:
                print(f"    {kernel}")

        print("\nGenerated C++ code for the first kernel:")
        print(CppExprCodeGenerator().generate_cpp_code(kernels[0]))

    # ── code generation ───────────────────────────────────────────────────────
    gen = FullCodeGenerator(kernels, main_func)

    cuda_path = output_dir / args.cuda_output
    cuda_path.write_text(gen.generate_cuda_code())

    cpp_path = output_dir / args.cpp_output
    cpp_path.write_text(gen.generate_pure_cpp_code())

    fortran_path = output_dir / args.fortran_output
    fortran_path.write_text(gen.generate_fortran_interface_code())

    print(f"Generated files in {output_dir}/")
    print(f"  cuda:              {cuda_path.name}")
    print(f"  c++:               {cpp_path.name}")
    print(f"  fortran interface: {fortran_path.name}")

    if not args.no_common_header:
        common_path = output_dir / args.common_header
        shutil.copy2(_TEMPLATES_DIR / "common_functions.cuh", common_path)
        print(f"  common header:     {common_path.name}")


if __name__ == "__main__":
    main()
