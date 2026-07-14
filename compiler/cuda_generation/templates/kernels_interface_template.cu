#include <cuda_runtime.h>
#include <cstddef>
#include <iostream>

#ifdef USE_PINNED_MEMORY
#include <unordered_set>
#endif

#define MEASURE_CUDA_EXECUTION_TIME
#include "common_functions.cuh"

using namespace generated_kernels::indexing;
using namespace generated_kernels::timing;

#ifdef USE_PINNED_MEMORY
std::unordered_set<void*> pinned_ptrs;
#endif

namespace generated_kernels {

$KERNEL_DEFINITIONS$

// The wrapper function called by Fortran
extern "C" {
    void cpp_start_hot() {
        reset_timing_vectors();
    }

    void cpp_finish_hot() {
        print_timing_summary();
    }

    void cpp_$KERNEL_NAME$(
        $HOST_PARAMETERS$
    ) {
        #ifdef USE_PINNED_MEMORY

        $PINNING_OF_HOST_BUFFERS$

        #endif // USE_PINNED_MEMORY

        // 1. Allocate memory on the GPU (Device)
        $DEVICE_BUFF_DECLS$

        measure_alloc([&]() {
            $MEMORY_ALLOCATIONS$
        });

        size_t total_h2d_bytes = $TOTAL_H2D_SIZE_CALCULATION$;

        // 2. Copy inputs from Host (CPU) to Device (GPU)
        measure_h2d(total_h2d_bytes, [&]() {
            $CUDA_H2D_COPY$
        });

        // Declare local variables
        $LOCAL_VAR_DECLS_IN_HOST_CODE$

        // 3. Launch the CUDA Kernels
        measure_kernel_executions([&]() {
            $KERNELS_LAUNCH$
        });

        // Wait for GPU to finish
        CUCH(cudaDeviceSynchronize());

        size_t total_d2h_bytes = $TOTAL_D2H_SIZE_CALCULATION$;

        // 5. Copy results back from Device (GPU) to Host (CPU)
        measure_d2h(total_d2h_bytes, [&]() {
            $CUDA_D2H_COPY$
        });


        // 6. Free the GPU memory
        measure_free([&]() {
            $MEMORY_FREES$
        });
    }
}
}