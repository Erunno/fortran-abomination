program cdv_benchmark
    use advection_module

    implicit none

    current(:,:) = 0

    call test_cuda_kernel(current, next)
    
    print *, next

end program array_slice
