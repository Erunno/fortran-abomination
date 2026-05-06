! kernels
module gol_module
    implicit none
    private

    public gol_kernel

    contains

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
    subroutine second_gol_kernel(current_grid, next_grid)
        implicit none

        integer, intent(in) :: current_grid(:,:)
        integer, intent(out) :: next_grid(:,:)

        integer :: i, j

        do i = 1, size(current_grid, 1)
            do j = 1, size(current_grid, 2)
                call third_gol_kernel(current_grid, next_grid, i, j)
            end do
        end do

    end subroutine second_gol_kernel

    ! kernel
    subroutine third_gol_kernel(in_arr, out_arr, ii, jj)
        implicit none

        integer, intent(in) :: in_arr(:,:)
        integer, intent(out) :: out_arr(:,:)
        integer, intent(in) :: ii, jj

        integer :: i

        out_arr(ii,jj) = in_arr(ii,jj) + ii + jj

        do i = 1, size(in_arr, 1)
            out_arr(ii,jj) = out_arr(ii,jj) + in_arr(i,jj)
        end do

    end subroutine third_gol_kernel

end module gol_module