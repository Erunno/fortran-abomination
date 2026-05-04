module gol_module
    implicit none
    private

    public gol_kernel

    contains

    ! entry kernel
    subroutine gol_kernel(current_grid, next_grid)
        implicit none

        integer, intent(in) :: current_grid(:,:)
        integer, intent(out) :: next_grid(:,:)

        integer :: i, j

        do i = 1, size(current_grid, 1)
            do j = 1, size(current_grid, 2)
                next_grid(i,j) = current_grid(i,j) + i
            end do
        end do

    end subroutine gol_kernel

end module gol_module