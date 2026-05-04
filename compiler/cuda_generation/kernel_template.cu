#include <cuda_runtime.h>

namespace __generated_kernels__ {
    __global__ void kernel_$KERNEL_ID$($PARAMETER_LIST$) {
        $KERNEL_BODY$
    }

    void call_kernel_$KERNEL_ID$($PARAMETER_LIST$) {
        
        dim3 blockSize($BLOCK_SIZE$);
        dim3 gridSize($GRID_SIZE$);

        kernel_$KERNEL_ID$<<<gridSize, blockSize>>>(
            $ARGUMENT_LIST$
        );
    }
}
