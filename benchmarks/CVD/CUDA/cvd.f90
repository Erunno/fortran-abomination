! kernels
module MomentumAdvection
  use iso_c_binding, only: c_double, c_int, c_size_t, c_ptr, c_loc
  implicit none
  private
  public CDV, knd, start_hot, finish_hot

  integer, parameter :: knd = c_double

  interface
    subroutine cpp_CDV( &
      v2, v2_dim1, v2_dim2, v2_dim3, &
      u, u_dim1, u_dim2, u_dim3, &
      v, v_dim1, v_dim2, v_dim3, &
      w, w_dim1, w_dim2, w_dim3, &
      dxmin, dymin, dzmin, vnx, vny, vnz) bind(C, name='cpp_CDV')
      import :: c_double, c_int, c_size_t, c_ptr
      type(c_ptr), value, intent(in) :: v2
      integer(c_size_t), value, intent(in) :: v2_dim1, v2_dim2, v2_dim3
      type(c_ptr), value, intent(in) :: u
      integer(c_size_t), value, intent(in) :: u_dim1, u_dim2, u_dim3
      type(c_ptr), value, intent(in) :: v
      integer(c_size_t), value, intent(in) :: v_dim1, v_dim2, v_dim3
      type(c_ptr), value, intent(in) :: w
      integer(c_size_t), value, intent(in) :: w_dim1, w_dim2, w_dim3
      real(c_double), value, intent(in) :: dxmin, dymin, dzmin
      integer(c_int), value, intent(in) :: vnx, vny, vnz
    end subroutine cpp_CDV
  end interface

contains

  ! ==========================================
  ! Main Entry Point
  ! ==========================================

  ! kernel
  subroutine CDV(V2, U, V, W, dxmin, dymin, dzmin, Vnx, Vny, Vnz)
    real(knd), contiguous, target, intent(out) :: V2(:,:,:)
    real(knd), contiguous, target, intent(in)  :: U(:,:,:), V(:,:,:), W(:,:,:)
    real(knd), intent(in) :: dxmin, dymin, dzmin
    integer, intent(in) :: Vnx, Vny, Vnz

    call cpp_CDV( &
      c_loc(V2(1,1,1)), int(size(V2,1), c_size_t), int(size(V2,2), c_size_t), int(size(V2,3), c_size_t), &
      c_loc(U(1,1,1)),  int(size(U,1),  c_size_t), int(size(U,2),  c_size_t), int(size(U,3),  c_size_t), &
      c_loc(V(1,1,1)),  int(size(V,1),  c_size_t), int(size(V,2),  c_size_t), int(size(V,3),  c_size_t), &
      c_loc(W(1,1,1)),  int(size(W,1),  c_size_t), int(size(W,2),  c_size_t), int(size(W,3),  c_size_t), &
      dxmin, dymin, dzmin, int(Vnx, c_int), int(Vny, c_int), int(Vnz, c_int))
    
  end subroutine CDV

  subroutine start_hot()
  end subroutine start_hot

  subroutine finish_hot()
  end subroutine finish_hot

end module MomentumAdvection