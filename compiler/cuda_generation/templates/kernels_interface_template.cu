#include <cuda_runtime.h>
#include <cstddef>
#include <iostream>

$KERNEL_DEFINITIONS$

// The wrapper function called by Fortran
extern "C" {
    void cpp_$KERNEL_NAME$(
        $HOST_PARAMETERS$
    ) {
        // 1. Allocate memory on the GPU (Device)
        $MEMORY_ALLOCATIONS$

        // 2. Copy inputs from Host (CPU) to Device (GPU)
        $MEMCPY_H2D$

        // 3. Launch the CUDA Kernels
        $KERNELS_LAUNCH$

        // Wait for GPU to finish
        cudaDeviceSynchronize();

        // 5. Copy results back from Device (GPU) to Host (CPU)
        $MEMCPY_D2H$

        // 6. Free the GPU memory
        $MEMORY_FREES$
    }
}