! kernels
module gol_module
    use, intrinsic :: iso_c_binding
    implicit none
    private

    public test_cuda_kernel



    contains

    ! kernel
    subroutine test_cuda_kernel(current_grid, next_grid)
        implicit none
        integer, intent(in) :: current_grid(:,:)
        integer, intent(out) :: next_grid(:,:)

        ! Define the C++ function signature so Fortran knows how to call it
        interface
            subroutine cpp_test_cuda_kernel(current, sz_c_1, sz_c_2, next, sz_n_1, sz_n_2) bind(C, name="cpp_test_cuda_kernel")
                import :: C_INT, C_SIZE_T
                
                ! Arrays are passed by reference (standard Fortran behavior)
                integer(C_INT), intent(in) :: current(*)
                integer(C_INT), intent(out) :: next(*)
                
                ! The 'value' attribute tells Fortran to pass these by value, matching C++ size_t
                integer(C_SIZE_T), value :: sz_c_1, sz_c_2
                integer(C_SIZE_T), value :: sz_n_1, sz_n_2
            end subroutine cpp_test_cuda_kernel
        end interface

        ! Call the C++ interface, passing the arrays and casting the sizes to C-compatible types
        call cpp_test_cuda_kernel( &
            current_grid, int(size(current_grid, 1), c_size_t), int(size(current_grid, 2), c_size_t), &
            next_grid, int(size(next_grid, 1), c_size_t), int(size(next_grid, 2), c_size_t) &
        )

    end subroutine test_cuda_kernel

    ! kernel
    subroutine gol_kernel(current_grid, next_grid)
        implicit none

        integer, intent(in) :: current_grid(:,:)
        integer, intent(out) :: next_grid(:,:)

        integer :: i, j, k(size(current_grid, 1) + 1)

        current_grid(1,1) = 42
        current_grid(1,2) = 42
        current_grid(1,5) = 42

        do i = 1, size(current_grid, 1)
            next_grid(i,5) = current_grid(i,5) + i
            
            do j = 1, size(current_grid, 2)
                next_grid(i,j) = current_grid(i,j) + i
                k(i) = k(i) + 1
            end do

            k(i) = k(i) + 5
        end do

        do i = 1, size(current_grid, 1)
            next_grid(i,42) = current_grid(i,5) + i
        end do

    end subroutine gol_kernel

    ! kernel
    subroutine second_gol_kernel(current_grid, next_grid, N)
        implicit none

        integer, intent(in) :: current_grid(:,:)
        integer, intent(out) :: next_grid(:,:)

        integer :: i, j, x, N

        ! x = 42

        do i = 1, size(current_grid, 1), 2
            do j = 1, N
                next_grid(i,j) = current_grid(i,j) + i + j + 1 + 1.2
                call third_gol_kernel(next_grid, next_grid, i, j)
            end do

            ! next_grid(i,42) = current_grid(i,5) + i
        end do

        do i = 1, size(next_grid, 1)
            next_grid(i,42) = next_grid(i,5) + i
        end do

    end subroutine second_gol_kernel

    ! kernel
    subroutine third_gol_kernel(in_arr, out_arr, ii, jj)
        implicit none

        integer, intent(in) :: in_arr(:,:)
        integer, intent(out) :: out_arr(:,:)
        integer, intent(in) :: ii, jj

        integer :: i

        ! out_arr(ii,jj) = in_arr(ii,jj) + ii + jj

        do i = 1, size(in_arr, 1)
            out_arr(ii,jj) = out_arr(ii,jj) + in_arr(i,jj)
        end do

    end subroutine third_gol_kernel

end module gol_module