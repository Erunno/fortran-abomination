{
    // 3. Define execution configuration

    // Define the primary iteration space size for the kernel grid
    $TOTAL_ELEMENTS$

    int threadsPerBlock = 256;
    int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
    
    // 4. Launch the CUDA kernel
    $KERNEL_NAME$_device<<<blocksPerGrid, threadsPerBlock>>>(
        $KERNEL_ARGS$,
        total_elements
    );
}