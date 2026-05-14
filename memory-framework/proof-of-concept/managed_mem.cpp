#include <iostream>
#include <csignal>
#include <sys/mman.h>
#include <unistd.h>
#include <cstdint>

// State for the actual array logic
int* g_in_arr = nullptr;
int* g_out_arr = nullptr;
int g_elements = 0;
bool g_evaluated = false;

// State for the OS Page Boundaries
void* g_in_page_start = nullptr;
size_t g_in_page_size = 0;
void* g_out_page_start = nullptr;
size_t g_out_page_size = 0;

extern "C" {

    void perform_lazy_doubling() {
        if (g_evaluated) return;
        g_evaluated = true;
        
        std::cout << "[C++ HOOK] Executing lazy doubling NOW!" << std::endl;
        
        for (int i = 0; i < g_elements; ++i) {
            g_out_arr[i] = g_in_arr[i] * 2;
        }
    }

    void segv_handler(int sig, siginfo_t *si, void *unused) {
        void* fault_addr = si->si_addr;
        
        bool in_input_page = (fault_addr >= g_in_page_start && 
                              fault_addr < (char*)g_in_page_start + g_in_page_size);
        bool in_output_page = (fault_addr >= g_out_page_start && 
                               fault_addr < (char*)g_out_page_start + g_out_page_size);

        if (!in_input_page && !in_output_page) {
            // Use bare-metal write here to be absolutely safe during a real crash
            const char msg[] = "Fatal: Real segfault somewhere else!\n";
            auto write_res = write(STDERR_FILENO, msg, sizeof(msg) - 1); (void)write_res;
            std::_Exit(1);
        }

        mprotect(g_in_page_start, g_in_page_size, PROT_READ | PROT_WRITE);
        mprotect(g_out_page_start, g_out_page_size, PROT_READ | PROT_WRITE);

        std::cout << "\n[C++ HOOK] Trap triggered at memory address: " << fault_addr << std::endl;
        
        // Now it is perfectly safe to perform our logic
        perform_lazy_doubling();
    }

    // Called once by Fortran to set the trap
    void arm_memory_locks(int* in_ptr, int* out_ptr, int elements) {
        g_in_arr = in_ptr;
        g_out_arr = out_ptr;
        g_elements = elements;
        g_evaluated = false;

        long page_size = sysconf(_SC_PAGESIZE);
        uintptr_t page_mask = ~(page_size - 1); 

        // 1. Calculate Page Boundaries for Input Array
        uintptr_t in_start = (uintptr_t)in_ptr;
        uintptr_t in_end = in_start + (elements * sizeof(int));
        g_in_page_start = (void*)(in_start & page_mask); 
        g_in_page_size = ((in_end + page_size - 1) & page_mask) - (uintptr_t)g_in_page_start;

        // 2. Calculate Page Boundaries for Output Array
        uintptr_t out_start = (uintptr_t)out_ptr;
        uintptr_t out_end = out_start + (elements * sizeof(int));
        g_out_page_start = (void*)(out_start & page_mask); 
        g_out_page_size = ((out_end + page_size - 1) & page_mask) - (uintptr_t)g_out_page_start;

        // 3. Apply memory protections to the WHOLE pages
        mprotect(g_in_page_start, g_in_page_size, PROT_READ);
        mprotect(g_out_page_start, g_out_page_size, PROT_NONE);

        // 4. Register the handler
        struct sigaction sa;
        sa.sa_flags = SA_SIGINFO;
        sigemptyset(&sa.sa_mask);
        sa.sa_sigaction = segv_handler;
        sigaction(SIGSEGV, &sa, NULL);
    }
}