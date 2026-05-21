# Lazy GPU Memory Framework

A proof-of-concept for **transparent, demand-driven GPU memory management** for
Fortran programs — no changes to Fortran source code required.

---

## The Problem

Across all three stencil kernels the GPU computation is ~40–60× faster than
serial Fortran, but host↔device data transfers consume ~91% of total CUDA
wall-clock time (see benchmark results).  The generated code currently copies
every input array to the GPU before each call and every output array back
afterwards — unconditionally, even if Fortran never reads the result.

---

## The Idea

Keep arrays as ordinary Fortran `allocate` memory.  Use `mprotect(2)` to
temporarily revoke CPU access rights to a buffer.  Any subsequent Fortran read
or write raises a `SIGSEGV`, which a custom signal handler intercepts, performs
the minimum necessary transfer (or skips it), restores access, and returns.
Fortran resumes unmodified.

The result is **lazy, pull-on-demand transfers**: a copy only happens when
Fortran actually touches the data, and only in the direction needed.

---

## Status

Proof of concept.  `proof-of-concept/` demonstrates the mechanism with a trivial
integer-doubling stand-in for the GPU kernel — no CUDA required.  See
[`proof-of-concept/README.md`](proof-of-concept/README.md) for build and run
instructions.

`include/mem_guard.hpp` sketches the intended production API; it is incomplete
and will evolve.

---

## Known Limitations

- `mprotect` is page-granular (4 096 bytes); small buffers or allocation
  boundaries may cause neighbouring arrays to share a protected page.
- `cudaMemcpy` inside a signal handler is not officially supported; a real
  implementation would likely defer transfers to a helper thread.
- Conflicts with other `SIGSEGV` handlers (MPI, OpenMP runtimes, profilers).
- Not thread-safe: `mprotect` affects all threads in the process.
