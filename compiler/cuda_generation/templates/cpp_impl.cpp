#include "common_functions.cuh"

namespace generated_kernels {

using namespace generated_kernels::indexing;

// The wrapper function called by Fortran
extern "C" {
    void cpp_start_hot() {
    }

    void cpp_finish_hot() {
    }

    void cpp_$KERNEL_NAME$(
        $HOST_PARAMETERS$
    ) {
        $LOCAL_VAR_DECLS$

        $KERNEL_BODY$
    }
}
}