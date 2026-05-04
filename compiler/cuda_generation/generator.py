from ..stencil_context import StencilContext

class CudaGenerator:
    def __init__(self, context):
        self.parse_tree = context.parse_tree

    def generate_cuda_code(self):
        # Placeholder for CUDA code generation logic
        cuda_code = "// CUDA code generated from Fortran\n"
        # Traverse the parse tree and generate CUDA code
        # This is where the main logic for code generation will go
        return cuda_code
    
print (StencilContext.hello)