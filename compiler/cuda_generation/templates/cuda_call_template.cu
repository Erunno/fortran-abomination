{
    // 3.$KERNEL_ID$ Define execution configuration

    // Define the primary iteration space size for the kernel grid
    size_t total_elements = $TOTAL_ELEMENTS$;

    int threadsPerBlock = $BLOCK_SIZE$;
    int blocksPerGrid = (total_elements + threadsPerBlock - 1) / threadsPerBlock;
    
    // 4. Launch the CUDA kernel
    $KERNEL_NAME$_device<<<blocksPerGrid, threadsPerBlock>>>(
        $KERNEL_ARGS$,
        total_elements
    );
}