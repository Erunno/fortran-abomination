module generated_kernels
  use iso_c_binding, only: c_double, c_int, c_size_t, c_ptr, c_loc
  implicit none
  private
  public CDV, knd, start_hot, finish_hot

  integer, parameter :: knd = c_double

  interface
    subroutine cpp_CDV( &
            u, u_dim1, u_dim2, u_dim3, &
            vnx, &
            v, v_dim1, v_dim2, v_dim3, &
            vny, &
            vnz, &
            w, w_dim1, w_dim2, w_dim3, &
            dxmin, &
            v2, v2_dim1, v2_dim2, v2_dim3, &
            dymin, &
            dzmin &
        ) bind(C, name='cpp_CDV')
      import :: c_double, c_int, c_size_t, c_ptr
        real(kind = knd), dimension(*) :: u
        integer(c_size_t), value, intent(in) :: u_dim1
        integer(c_size_t), value, intent(in) :: u_dim2
        integer(c_size_t), value, intent(in) :: u_dim3
        integer(c_int), value, intent(in) :: vnx
        real(kind = knd), dimension(*) :: v
        integer(c_size_t), value, intent(in) :: v_dim1
        integer(c_size_t), value, intent(in) :: v_dim2
        integer(c_size_t), value, intent(in) :: v_dim3
        integer(c_int), value, intent(in) :: vny
        integer(c_int), value, intent(in) :: vnz
        real(kind = knd), dimension(*) :: w
        integer(c_size_t), value, intent(in) :: w_dim1
        integer(c_size_t), value, intent(in) :: w_dim2
        integer(c_size_t), value, intent(in) :: w_dim3
        real(kind = knd), value, intent(in) :: dxmin
        real(kind = knd), dimension(*) :: v2
        integer(c_size_t), value, intent(in) :: v2_dim1
        integer(c_size_t), value, intent(in) :: v2_dim2
        integer(c_size_t), value, intent(in) :: v2_dim3
        real(kind = knd), value, intent(in) :: dymin
        real(kind = knd), value, intent(in) :: dzmin
    end subroutine cpp_CDV

    subroutine cpp_start_hot() bind(C, name='cpp_start_hot')
    end subroutine cpp_start_hot

    subroutine cpp_finish_hot() bind(C, name='cpp_finish_hot')
    end subroutine cpp_finish_hot
  end interface

contains

  ! ==========================================
  ! Main Entry Point
  ! ==========================================

  subroutine CDV( &
        $ORIGINAL_FORTRAN_KERNEL_ARGS$
    )
    $FORTRAN_KERNEL_ARGS_DECLS$

    call cpp_CDV( &
        $FORTRAN_CPP_KERNEL_ARGS_CALL$
    )
    
  end subroutine CDV

  subroutine start_hot()
    call cpp_start_hot()
  end subroutine start_hot

  subroutine finish_hot()
    call cpp_finish_hot()
  end subroutine finish_hot

end module generated_kernels