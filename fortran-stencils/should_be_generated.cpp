#include <cstddef>

// Fortran arrays are column-major. The contiguous dimension is the first one (i).
// Memory offset = j * size_i + i
#define IDX_COL_MAJOR(i, j, size_i) ((j) * (size_i) + (i))

// extern "C" stops C++ from mangling the function name so Fortran can find it
extern "C" {
    void cpp_test_cuda_kernel(
        const int* current_grid,
        size_t size_current_grid_0,
        size_t size_current_grid_1,

        int* next_grid,
        size_t size_next_grid_0,
        size_t size_next_grid_1
    ) {
        for (size_t i = 0; i < size_current_grid_0; ++i) {
            for (size_t j = 0; j < size_current_grid_1; ++j) {
                
                // + (i + 1) + (j + 1) mimics Fortran's 1-based loop counters
                next_grid[IDX_COL_MAJOR(i, j, size_next_grid_0)] = 
                    current_grid[IDX_COL_MAJOR(i, j, size_current_grid_0)] + (i + 1) + (j + 1);
            }
        }
    }
}