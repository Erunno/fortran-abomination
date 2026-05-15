#include <cuda_runtime.h>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <vector>
// #define MEASURE_CUDA_EXECUTION_TIME
#include "common_functions.cuh"

using namespace generated_kernels::indexing;
using namespace generated_kernels::timing;

namespace generated_kernels {

__global__ 
void kernel_group_1_device(
    int vnx,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vny,
    int vnz,
    double zero,
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
    int k;
    int j;
    int i;

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
    int vnx,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    double ax,
    int vny,
    double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
    double ay,
    int vnz,
    double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
    double az,
    double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
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
    int j;
    int k;
    int i;

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
    double ax,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vnx,
    double ay,
    double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
    int vny,
    double az,
    double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
    int vnz,
    double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
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
    double wadv;
    int i;
    int j;
    int k;
    double uadv;

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
    int vnx,
    double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
    int vny,
    int vnz,
    double half,
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
    int k;
    int j;
    int i;

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
        double* v2, size_t v2_dim1, size_t v2_dim2, size_t v2_dim3,
        double* u, size_t u_dim1, size_t u_dim2, size_t u_dim3,
        double* v, size_t v_dim1, size_t v_dim2, size_t v_dim3,
        double* w, size_t w_dim1, size_t w_dim2, size_t w_dim3,
        double dxmin,
        double dymin,
        double dzmin,
        int vnx,
        int vny,
        int vnz
    ) {
        const std::size_t v2_bytes = sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3;
        const std::size_t u_bytes = sizeof(double) * u_dim1 * u_dim2 * u_dim3;
        const std::size_t v_bytes = sizeof(double) * v_dim1 * v_dim2 * v_dim3;
        const std::size_t w_bytes = sizeof(double) * w_dim1 * w_dim2 * w_dim3;

        const std::uint64_t zero_fill_bytes = static_cast<std::uint64_t>(v2_bytes) + static_cast<std::uint64_t>(u_bytes) +
                                              static_cast<std::uint64_t>(v_bytes) + static_cast<std::uint64_t>(w_bytes);
        const std::uint64_t h2d_bytes = zero_fill_bytes;
        const std::uint64_t d2h_bytes = static_cast<std::uint64_t>(v2_bytes);

        double* v2_device = nullptr;
        double* u_device = nullptr;
        double* v_device = nullptr;
        double* w_device = nullptr;

        measure_alloc([&]() {
            cudaMalloc(&v2_device, (sizeof(double) * v2_dim1 * v2_dim2 * v2_dim3));
            cudaMalloc(&u_device, (sizeof(double) * u_dim1 * u_dim2 * u_dim3));
            cudaMalloc(&v_device, (sizeof(double) * v_dim1 * v_dim2 * v_dim3));
            cudaMalloc(&w_device, (sizeof(double) * w_dim1 * w_dim2 * w_dim3));
        });

        measure_h2d(h2d_bytes, [&]() {
            cudaMemcpy(v2_device, v2, v2_bytes, cudaMemcpyHostToDevice);
            cudaMemcpy(u_device, u, u_bytes, cudaMemcpyHostToDevice);
            cudaMemcpy(v_device, v, v_bytes, cudaMemcpyHostToDevice);
            cudaMemcpy(w_device, w, w_bytes, cudaMemcpyHostToDevice);
        });

        // Declare local variables
        double az;
        double half;
        double ax;
        double ay;
        double zero;

        zero = 0.0;
        half = 0.5;

        measure_kernels_execution([&]() {
            {
                size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
                int threadsPerBlock = 256;
                int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
                int k_from = 2;
                int k_to = (vnz + 1);
                int j_from = 2;
                int j_to = (vny + 1);
                int i_from = 2;
                int i_to = (vnx + 1);

                kernel_group_1_device<<<blocksPerGrid, threadsPerBlock>>>(
                    vnx,
                    v2_device, v2_dim1, v2_dim2, v2_dim3,
                    vny,
                    vnz,
                    zero,
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
                size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
                int threadsPerBlock = 256;
                int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
                int k_from = 2;
                int k_to = (vnz + 1);
                int j_from = 2;
                int j_to = (vny + 1);
                int i_from = 2;
                int i_to = (vnx + 1);

                kernel_group_3_device<<<blocksPerGrid, threadsPerBlock>>>(
                    vnx,
                    v2_device, v2_dim1, v2_dim2, v2_dim3,
                    ax,
                    vny,
                    u_device, u_dim1, u_dim2, u_dim3,
                    ay,
                    vnz,
                    v_device, v_dim1, v_dim2, v_dim3,
                    az,
                    w_device, w_dim1, w_dim2, w_dim3,
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
                size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
                int threadsPerBlock = 256;
                int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
                int k_from = 2;
                int k_to = (vnz + 1);
                int j_from = 2;
                int j_to = (vny + 1);
                int i_from = 2;
                int i_to = (vnx + 1);

                kernel_group_5_device<<<blocksPerGrid, threadsPerBlock>>>(
                    ax,
                    v2_device, v2_dim1, v2_dim2, v2_dim3,
                    vnx,
                    ay,
                    u_device, u_dim1, u_dim2, u_dim3,
                    vny,
                    az,
                    v_device, v_dim1, v_dim2, v_dim3,
                    vnz,
                    w_device, w_dim1, w_dim2, w_dim3,
                    k_from, k_to,
                    j_from, j_to,
                    i_from, i_to,
                    total_elements
                );
            }

            {
                size_t total_elements = (((vnz + 1) - 2 + 1) * ((vny + 1) - 2 + 1) * ((vnx + 1) - 2 + 1));
                int threadsPerBlock = 256;
                int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
                int k_from = 2;
                int k_to = (vnz + 1);
                int j_from = 2;
                int j_to = (vny + 1);
                int i_from = 2;
                int i_to = (vnx + 1);

                kernel_group_6_device<<<blocksPerGrid, threadsPerBlock>>>(
                    vnx,
                    v2_device, v2_dim1, v2_dim2, v2_dim3,
                    vny,
                    vnz,
                    half,
                    k_from, k_to,
                    j_from, j_to,
                    i_from, i_to,
                    total_elements
                );
            }
        });

        measure_d2h(d2h_bytes, [&]() {
            cudaMemcpy(v2, v2_device, v2_bytes, cudaMemcpyDeviceToHost);
        });


        measure_free([&]() {
            cudaFree(v2_device);
            cudaFree(u_device);
            cudaFree(v_device);
            cudaFree(w_device);
        });
    }
}
}