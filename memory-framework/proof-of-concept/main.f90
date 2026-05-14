program native_fortran_lazy
    use iso_c_binding
    implicit none

    interface
        subroutine arm_memory_locks(in_ptr, out_ptr, elements) bind(C, name="arm_memory_locks")
            import :: c_int
            integer(c_int), dimension(*), intent(inout) :: in_ptr, out_ptr
            integer(c_int), value :: elements
        end subroutine
    end interface

    integer(c_int), allocatable, target :: in_arr(:), out_arr(:)
    integer(c_int) :: num_elements = 5000 
    
    character(len=10) :: arg
    integer :: test_case

    ! 1. Parse Command Line Argument
    if (command_argument_count() < 1) then
        print *, "Please provide a test case number (1, 2, 3, or 4)"
        print *, "  1 = Read Input (Allowed)"
        print *, "  2 = Write Input (Triggers Hook)"
        print *, "  3 = Read Output (Triggers Hook)"
        print *, "  4 = Write Output (Triggers Hook)"
        stop
    end if
    
    call get_command_argument(1, arg)
    read(arg, *) test_case

    ! 2. Standard Fortran Setup
    allocate(in_arr(num_elements))
    allocate(out_arr(num_elements))
    in_arr(1) = 15
    in_arr(2) = 30
    
    ! 3. Arm the locks
    call arm_memory_locks(in_arr, out_arr, num_elements)

    ! 4. Execute ONLY the requested test
    select case (test_case)
        
        case (1)
            print *, "--- TEST 1: Reading Input ---"
            print *, "Action: Reading in_arr(1)"
            print *, "Result: ", in_arr(1)
            print *, "Expected: 15. No hook fired."
            
        case (2)
            print *, "--- TEST 2: Writing Input ---"
            print *, "Action: in_arr(1) = 999"
            in_arr(1) = 999 ! Hook fires here!
            print *, "Result: in_arr(1) = ", in_arr(1)
            print *, "Result: in_arr(2) = ", in_arr(2)
            print *, "Result: out_arr(1)= ", out_arr(1)
            print *, "Result: out_arr(2)= ", out_arr(2)
            print *, "Expected: Hook fired. out_arr(1) is 30 (doubled from original 15)."
            
        case (3)
            print *, "--- TEST 3: Reading Output ---"
            print *, "Action: Reading out_arr(1)"
            print *, "Result: ", out_arr(1) ! Hook fires here!
            print *, "Result: out_arr(2) = ", out_arr(2)
            print *, "Expected: Hook fired. Result is 30."

        case (4)
            print *, "--- TEST 4: Writing Output ---"
            print *, "Action: out_arr(1) = 888"
            out_arr(1) = 888 ! Hook fires here!
            print *, "Result: out_arr(1) = ", out_arr(1)
            print *, "Result: out_arr(2) = ", out_arr(2)
            print *, "Expected: Hook fired. out_arr(1) is 888 (overwritten), but out_arr(2) is safely 60."

        case default
            print *, "Invalid test case."
    end select

    deallocate(in_arr)
    deallocate(out_arr)

end program native_fortran_lazy