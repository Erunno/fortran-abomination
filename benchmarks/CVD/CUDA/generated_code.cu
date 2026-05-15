#include <cuda_runtime.h>
#include <cstddef>
#include <iostream>

#define MEASURE_CUDA_EXECUTION_TIME
#include "common_functions.cuh"

using namespace generated_kernels::indexing;
using namespace generated_kernels::timing;

namespace generated_kernels {

__global__ 
void kernel_group_1_device(
    double zero,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vny,
    int vnz,
    int vnx,
    int k_from, int k_to,
    int j_from, int j_to,
    int i_from, int i_to,
    size_t total_elements
) {
    // 1D Thread Index
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure we don't go out of bounds
    if (idx >= total_elements) {
        return;
    }

    // Declarations of local variables used in the kernel body
    int i;
    int j;
    int k;

    // Map the 1D index back to column-major multi-dimensional coordinates
    constexpr int k_step = 1;
        constexpr int j_step = 1;
        constexpr int i_step = 1;
    size_t current_idx = idx;
    
    // Calculate index for 'i' dimension
    int num_i = ((i_to - i_from + i_step) / i_step);
    int local_i = current_idx % num_i;
    i = i_from + local_i * i_step;
    current_idx /= num_i;
    
    // Calculate index for 'j' dimension
    int num_j = ((j_to - j_from + j_step) / j_step);
    int local_j = current_idx % num_j;
    j = j_from + local_j * j_step;
    current_idx /= num_j;
    
    // Calculate index for 'k' dimension
    int num_k = ((k_to - k_from + k_step) / k_step);
    int local_k = current_idx;
    k = k_from + local_k * k_step;

    // Perform the calculation
    v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] = zero;
    
}

__global__ 
void kernel_group_3_device(
    double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
    double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
    double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vny,
    double ay,
    int vnz,
    double az,
    double ax,
    int vnx,
    int k_from, int k_to,
    int j_from, int j_to,
    int i_from, int i_to,
    size_t total_elements
) {
    // 1D Thread Index
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure we don't go out of bounds
    if (idx >= total_elements) {
        return;
    }

    // Declarations of local variables used in the kernel body
    int i;
    int j;
    int k;

    // Map the 1D index back to column-major multi-dimensional coordinates
    constexpr int k_step = 1;
        constexpr int j_step = 1;
        constexpr int i_step = 1;
    size_t current_idx = idx;
    
    // Calculate index for 'i' dimension
    int num_i = ((i_to - i_from + i_step) / i_step);
    int local_i = current_idx % num_i;
    i = i_from + local_i * i_step;
    current_idx /= num_i;
    
    // Calculate index for 'j' dimension
    int num_j = ((j_to - j_from + j_step) / j_step);
    int local_j = current_idx % num_j;
    j = j_from + local_j * j_step;
    current_idx /= num_j;
    
    // Calculate index for 'k' dimension
    int num_k = ((k_to - k_from + k_step) / k_step);
    int local_k = current_idx;
    k = k_from + local_k * k_step;

    // Perform the calculation
    v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] = (-(((((((ay * ((v[F_IDX(i, (j + 1), k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)]))) * ((v[F_IDX(i, (j + 1), k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)]))) - ((ay * ((v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, (j - 1), k, v_dim1, v_dim2, v_dim3)]))) * ((v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, (j - 1), k, v_dim1, v_dim2, v_dim3)]))))) + ((((ax * ((v[F_IDX((i + 1), j, k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)]))) * ((u[F_IDX(i, (j + 1), k, u_dim1, u_dim2, u_dim3)] + u[F_IDX(i, j, k, u_dim1, u_dim2, u_dim3)]))) - ((ax * ((v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)] + v[F_IDX((i - 1), j, k, v_dim1, v_dim2, v_dim3)]))) * ((u[F_IDX((i - 1), (j + 1), k, u_dim1, u_dim2, u_dim3)] + u[F_IDX((i - 1), j, k, u_dim1, u_dim2, u_dim3)])))))) + ((((az * ((v[F_IDX(i, j, (k + 1), v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)]))) * ((w[F_IDX(i, (j + 1), k, w_dim1, w_dim2, w_dim3)] + w[F_IDX(i, j, k, w_dim1, w_dim2, w_dim3)]))) - ((az * ((v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)] + v[F_IDX(i, j, (k - 1), v_dim1, v_dim2, v_dim3)]))) * ((w[F_IDX(i, (j + 1), (k - 1), w_dim1, w_dim2, w_dim3)] + w[F_IDX(i, j, (k - 1), w_dim1, w_dim2, w_dim3)]))))))));
    
}

__global__ 
void kernel_group_5_device(
    double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
    double ay,
    double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
    int vny,
    double az,
    int vnz,
    double ax,
    int vnx,
    int k_from, int k_to,
    int j_from, int j_to,
    int i_from, int i_to,
    size_t total_elements
) {
    // 1D Thread Index
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure we don't go out of bounds
    if (idx >= total_elements) {
        return;
    }

    // Declarations of local variables used in the kernel body
    double uadv;
    double wadv;
    int i;
    int j;
    int k;

    // Map the 1D index back to column-major multi-dimensional coordinates
    constexpr int k_step = 1;
        constexpr int j_step = 1;
        constexpr int i_step = 1;
    size_t current_idx = idx;
    
    // Calculate index for 'i' dimension
    int num_i = ((i_to - i_from + i_step) / i_step);
    int local_i = current_idx % num_i;
    i = i_from + local_i * i_step;
    current_idx /= num_i;
    
    // Calculate index for 'j' dimension
    int num_j = ((j_to - j_from + j_step) / j_step);
    int local_j = current_idx % num_j;
    j = j_from + local_j * j_step;
    current_idx /= num_j;
    
    // Calculate index for 'k' dimension
    int num_k = ((k_to - k_from + k_step) / k_step);
    int local_k = current_idx;
    k = k_from + local_k * k_step;

    // Perform the calculation
    uadv = ((((u[F_IDX(i, j, k, u_dim1, u_dim2, u_dim3)] + u[F_IDX(i, (j + 1), k, u_dim1, u_dim2, u_dim3)]) + u[F_IDX((i - 1), j, k, u_dim1, u_dim2, u_dim3)]) + u[F_IDX((i - 1), (j + 1), k, u_dim1, u_dim2, u_dim3)]));
    wadv = ((((w[F_IDX(i, j, k, w_dim1, w_dim2, w_dim3)] + w[F_IDX(i, (j + 1), k, w_dim1, w_dim2, w_dim3)]) + w[F_IDX(i, j, (k - 1), w_dim1, w_dim2, w_dim3)]) + w[F_IDX(i, (j + 1), (k - 1), w_dim1, w_dim2, w_dim3)]));
    v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] = (v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] - (((((ax * ((v[F_IDX((i + 1), j, k, v_dim1, v_dim2, v_dim3)] - v[F_IDX((i - 1), j, k, v_dim1, v_dim2, v_dim3)]))) * uadv) + ((ay * ((v[F_IDX(i, (j + 1), k, v_dim1, v_dim2, v_dim3)] - v[F_IDX(i, (j - 1), k, v_dim1, v_dim2, v_dim3)]))) * v[F_IDX(i, j, k, v_dim1, v_dim2, v_dim3)])) + ((az * ((v[F_IDX(i, j, (k + 1), v_dim1, v_dim2, v_dim3)] - v[F_IDX(i, j, (k - 1), v_dim1, v_dim2, v_dim3)]))) * wadv))));
    
}

__global__ 
void kernel_group_6_device(
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vny,
    double half,
    int vnz,
    int vnx,
    int k_from, int k_to,
    int j_from, int j_to,
    int i_from, int i_to,
    size_t total_elements
) {
    // 1D Thread Index
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure we don't go out of bounds
    if (idx >= total_elements) {
        return;
    }

    // Declarations of local variables used in the kernel body
    int i;
    int j;
    int k;

    // Map the 1D index back to column-major multi-dimensional coordinates
    constexpr int k_step = 1;
        constexpr int j_step = 1;
        constexpr int i_step = 1;
    size_t current_idx = idx;
    
    // Calculate index for 'i' dimension
    int num_i = ((i_to - i_from + i_step) / i_step);
    int local_i = current_idx % num_i;
    i = i_from + local_i * i_step;
    current_idx /= num_i;
    
    // Calculate index for 'j' dimension
    int num_j = ((j_to - j_from + j_step) / j_step);
    int local_j = current_idx % num_j;
    j = j_from + local_j * j_step;
    current_idx /= num_j;
    
    // Calculate index for 'k' dimension
    int num_k = ((k_to - k_from + k_step) / k_step);
    int local_k = current_idx;
    k = k_from + local_k * k_step;

    // Perform the calculation
    v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] = (v2[F_IDX(i, j, k, v2_dim1, v2_dim2, v2_dim3)] * half);
    
}


// The wrapper function called by Fortran
extern "C" {
    void cpp_start_hot() {
        reset_timing_vectors();
    }

    void cpp_finish_hot() {
        print_timing_summary();
    }

    void cpp_CDV(
        double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
        double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
        double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
        int vnx,
        int vny,
        int vnz,
        double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
        double dxmin,
        double dymin,
        double dzmin
    ) {
        // 1. Allocate memory on the GPU (Device)
        double* v_device;
        double* w_device;
        double* v2_device;
        double* u_device;

        measure_alloc([&]() {
        cudaMalloc(&v_device, (sizeof(double) * v_dim1 * v_dim2 * v_dim3));
        cudaMalloc(&w_device, (sizeof(double) * w_dim1 * w_dim2 * w_dim3));
        cudaMalloc(&v2_device, (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3));
        cudaMalloc(&u_device, (sizeof(double) * u_dim1 * u_dim2 * u_dim3));
        });

        size_t total_h2d_bytes = (sizeof(double) * v_dim1 * v_dim2 * v_dim3) + (sizeof(double) * w_dim1 * w_dim2 * w_dim3) + (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3) + (sizeof(double) * u_dim1 * u_dim2 * u_dim3);

        // 2. Copy inputs from Host (CPU) to Device (GPU)
        measure_h2d(total_h2d_bytes, [&]() {
        cudaMemcpy(v_device, v, (sizeof(double) * v_dim1 * v_dim2 * v_dim3), cudaMemcpyHostToDevice);
        cudaMemcpy(w_device, w, (sizeof(double) * w_dim1 * w_dim2 * w_dim3), cudaMemcpyHostToDevice);
        cudaMemcpy(v2_device, v2, (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3), cudaMemcpyHostToDevice);
        cudaMemcpy(u_device, u, (sizeof(double) * u_dim1 * u_dim2 * u_dim3), cudaMemcpyHostToDevice);
        });

        // Declare local variables
        double half;
        double ay;
        double ax;
        double az;
        double zero;

        // 3. Launch the CUDA Kernels
        measure_kernel_executions([&]() {
        zero = 0.0;
        half = 0.5;
        {
            // 3.1 Define execution configuration
        
            // Define the primary iteration space size for the kernel grid
            size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
        
            int threadsPerBlock = 256;
            int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
            
            int k_from = 2;
            int k_to = (vnz + 1);
            
            int j_from = 2;
            int j_to = (vny + 1);
            
            int i_from = 2;
            int i_to = (vnx + 1);
        
            // 4. Launch the CUDA kernel
            kernel_group_1_device<<<blocksPerGrid, threadsPerBlock>>>(
                zero,
                v2_device, v2_dim1, v2_dim2, v2_dim3,
                vny,
                vnz,
                vnx,
                k_from, k_to,
                j_from, j_to,
                i_from, i_to,
                total_elements
            );
        }
        ax = (0.25 / dxmin);
        ay = (0.25 / dymin);
        az = (0.25 / dzmin);
        {
            // 3.3 Define execution configuration
        
            // Define the primary iteration space size for the kernel grid
            size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
        
            int threadsPerBlock = 256;
            int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
            
            int k_from = 2;
            int k_to = (vnz + 1);
            
            int j_from = 2;
            int j_to = (vny + 1);
            
            int i_from = 2;
            int i_to = (vnx + 1);
        
            // 4. Launch the CUDA kernel
            kernel_group_3_device<<<blocksPerGrid, threadsPerBlock>>>(
                u_device, u_dim1, u_dim2, u_dim3,
                w_device, w_dim1, w_dim2, w_dim3,
                v_device, v_dim1, v_dim2, v_dim3,
                v2_device, v2_dim1, v2_dim2, v2_dim3,
                vny,
                ay,
                vnz,
                az,
                ax,
                vnx,
                k_from, k_to,
                j_from, j_to,
                i_from, i_to,
                total_elements
            );
        }
        ax = (0.125 / dxmin);
        ay = (0.5 / dymin);
        az = (0.125 / dzmin);
        {
            // 3.5 Define execution configuration
        
            // Define the primary iteration space size for the kernel grid
            size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
        
            int threadsPerBlock = 256;
            int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
            
            int k_from = 2;
            int k_to = (vnz + 1);
            
            int j_from = 2;
            int j_to = (vny + 1);
            
            int i_from = 2;
            int i_to = (vnx + 1);
        
            // 4. Launch the CUDA kernel
            kernel_group_5_device<<<blocksPerGrid, threadsPerBlock>>>(
                u_device, u_dim1, u_dim2, u_dim3,
                ay,
                v_device, v_dim1, v_dim2, v_dim3,
                v2_device, v2_dim1, v2_dim2, v2_dim3,
                w_device, w_dim1, w_dim2, w_dim3,
                vny,
                az,
                vnz,
                ax,
                vnx,
                k_from, k_to,
                j_from, j_to,
                i_from, i_to,
                total_elements
            );
        }
        {
            // 3.6 Define execution configuration
        
            // Define the primary iteration space size for the kernel grid
            size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
        
            int threadsPerBlock = 256;
            int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
            
            int k_from = 2;
            int k_to = (vnz + 1);
            
            int j_from = 2;
            int j_to = (vny + 1);
            
            int i_from = 2;
            int i_to = (vnx + 1);
        
            // 4. Launch the CUDA kernel
            kernel_group_6_device<<<blocksPerGrid, threadsPerBlock>>>(
                v2_device, v2_dim1, v2_dim2, v2_dim3,
                vny,
                half,
                vnz,
                vnx,
                k_from, k_to,
                j_from, j_to,
                i_from, i_to,
                total_elements
            );
        }
        });

        // Wait for GPU to finish
        cudaDeviceSynchronize();

        size_t total_d2h_bytes = (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3);

        // 5. Copy results back from Device (GPU) to Host (CPU)
        measure_d2h(total_d2h_bytes, [&]() {
        cudaMemcpy(v2, v2_device, (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3), cudaMemcpyDeviceToHost);
        });


        // 6. Free the GPU memory
        measure_free([&]() {
        cudaFree(v_device);
        cudaFree(w_device);
        cudaFree(v2_device);
        cudaFree(u_device);
        });
    }
}
}