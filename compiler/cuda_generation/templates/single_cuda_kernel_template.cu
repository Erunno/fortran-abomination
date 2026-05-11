__global__ 
void $KERNEL_NAME$_device(
    $DEVICE_PARAMETERS$,
    size_t total_elements
) {
    // 1D Thread Index
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;

    // Ensure we don't go out of bounds
    if (idx >= total_elements) {
        return;
    }

    // Map the 1D index back to column-major multi-dimensional coordinates
    $INDEX_MAPPING_LOGIC$

    // Perform the calculation
    $KERNEL_BODY$
}
