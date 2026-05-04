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

        do i = 1, size(current_grid, 1)
            do j = 1, size(current_grid, 2)
                next_grid(i,j) = current_grid(i,j) + i
                k(i) = k(i) + 1
            end do
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
                next_grid(i,j) = current_grid(i,j) + j
            end do
        end do

    end subroutine second_gol_kernel

end module gol_module