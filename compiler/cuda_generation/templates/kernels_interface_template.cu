#include <cuda_runtime.h>
#include <cstddef>
#include <iostream>

namespace generated_kernels {

template <size_t Step, size_t N>
struct StaticLoop {
    __device__ __forceinline__ static void iterate(const size_t* arr, size_t& linear_idx, size_t& stride) {
        size_t current_index = arr[Step] - 1;
        size_t current_dim_size = arr[Step + N];

        linear_idx += current_index * stride;
        stride *= current_dim_size;

        StaticLoop<Step + 1, N>::iterate(arr, linear_idx, stride);
    }
};

template <size_t N>
struct StaticLoop<N, N> {
    __device__ __forceinline__ static void iterate(const size_t* arr, size_t& linear_idx, size_t& stride) {
        // Do nothing. The loop is finished.
    }
};

template <typename... Args>
__device__ __forceinline__ size_t F_IDX(Args... args) {
    constexpr size_t total_args = sizeof...(Args);
    
    static_assert(total_args % 2 == 0, "IDX requires N indices followed by N dimensions.");
    static_assert(total_args > 0, "IDX requires at least 2 arguments.");
    
    constexpr size_t N = total_args / 2;

    const size_t arr[total_args] = { static_cast<size_t>(args)... };

    size_t linear_idx = 0;
    size_t stride = 1;

    StaticLoop<0, N>::iterate(arr, linear_idx, stride);

    return linear_idx;
}

$KERNEL_DEFINITIONS$

// The wrapper function called by Fortran
extern "C" {
    void cpp_$KERNEL_NAME$(
        $HOST_PARAMETERS$
    ) {
        // 1. Allocate memory on the GPU (Device)
        $MEMORY_ALLOCATIONS$

        // 2. Copy inputs from Host (CPU) to Device (GPU)
        $CUDA_H2D_COPY$

        // 3. Launch the CUDA Kernels
        $KERNELS_LAUNCH$

        // Wait for GPU to finish
        cudaDeviceSynchronize();

        // 5. Copy results back from Device (GPU) to Host (CPU)
        $CUDA_D2H_COPY$

        // 6. Free the GPU memory
        $MEMORY_FREES$
    }
}
}