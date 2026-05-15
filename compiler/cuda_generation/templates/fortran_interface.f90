module $MODULE_NAME$
  use iso_c_binding, only: c_double, c_int, c_size_t, c_ptr, c_loc
  implicit none
  private
  public $KERNEL_NAME$, knd, start_hot, finish_hot

  integer, parameter :: knd = c_double

  interface
    subroutine cpp_$KERNEL_NAME$( &
        $FORTRAN_INTERFACE_DUMMY$ &
        ) bind(C, name='cpp_$KERNEL_NAME$')
      import :: c_double, c_int, c_size_t, c_ptr
      $FORTRAN_INTERFACE_DECLS$
    end subroutine cpp_$KERNEL_NAME$

    subroutine cpp_start_hot() bind(C, name='cpp_start_hot')
    end subroutine cpp_start_hot

    subroutine cpp_finish_hot() bind(C, name='cpp_finish_hot')
    end subroutine cpp_finish_hot
  end interface

contains

  ! ==========================================
  ! Main Entry Point
  ! ==========================================

  subroutine $KERNEL_NAME$( &
        $ORIGINAL_FORTRAN_KERNEL_ARGS$
    )
    $FORTRAN_KERNEL_ARGS_DECLS$

    call cpp_$KERNEL_NAME$( &
        $FORTRAN_CPP_KERNEL_ARGS_CALL$
    )
    
  end subroutine $KERNEL_NAME$

  subroutine start_hot()
    call cpp_start_hot()
  end subroutine start_hot

  subroutine finish_hot()
    call cpp_finish_hot()
  end subroutine finish_hot

end module $MODULE_NAME$