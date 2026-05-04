program array_slice
    use gol_module 

    implicit none

    integer :: current(10,10), next(10,10)

    current(:,:) = 0

    call gol_kernel(current, next)

    print *, next

end program array_slice
