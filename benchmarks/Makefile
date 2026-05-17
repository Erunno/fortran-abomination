# ============================================================
# Benchmarks — unified top-level Makefile
#
# Usage:
#   make CASE=CVD VARIANT=Fortran
#   make CASE=CVD VARIANT=CUDA NX=128 NY=128 NZ=128 NITER=200 NWARMUP=10
#   make CASE=CDU VARIANT=Fortran-OMP NX=256
#   make CASE=CDU VARIANT=CPP
#   make CASE=CDU VARIANT=CPP-OMP NX=256
#   make clean CASE=CVD VARIANT=Fortran
#   make clean-all                          # wipe the entire bin/ tree
#
# Required:
#   CASE    — subdirectory with the benchmark (CDU | CDW | CVD | …)
#
# Optional (all have defaults in common/defaults.mk):
#   VARIANT       — Fortran (default) | Fortran-OMP | CUDA | CPP | CPP-OMP
#   NX NY NZ      — interior grid dimensions
#   NITER         — timed iterations
#   NWARMUP       — warm-up iterations
#   FC FFLAGS     — Fortran compiler and base flags
#   EXTRA_FFLAGS  — appended to FFLAGS (handy for one-off flags)
#   CXX CXXFLAGS  — C++ compiler and base flags (CPP / CPP-OMP variants)
#   EXTRA_CXXFLAGS — appended to CXXFLAGS
#   CUDA_HOME NVCC NVCCFLAGS CUDA_ARCH
# ============================================================

CASE    ?= CVD
VARIANT ?= Fortran

include common/defaults.mk

# Each CASE/ directory contains a tiny case.mk that sets:
#   CASE_SRC        — the Fortran source filename  (e.g. cvd.f90)
#   CASE_CUDA_EXTRA — extra .cu files for CUDA variant (optional)
#   CASE_CPP_EXTRA  — extra .cpp files for CPP / CPP-OMP variant (optional)
include $(CASE)/case.mk

include common/variants.mk

# ---- Derived variables -------------------------------------
DEFINES      = -DVAR_NX=$(NX) -DVAR_NY=$(NY) -DVAR_NZ=$(NZ) \
               -DVAR_NITER=$(NITER) -DVAR_NWARMUP=$(NWARMUP)
ALL_FFLAGS   = $(FFLAGS) $(EXTRA_FFLAGS) $(VARIANT_FFLAGS) -cpp
ALL_CXXFLAGS = $(CXXFLAGS) $(EXTRA_CXXFLAGS) $(VARIANT_CXXFLAGS)

BUILD_ID    = $(CASE)_$(VARIANT)_NX$(NX)_NY$(NY)_NZ$(NZ)_NITER$(NITER)_NWARMUP$(NWARMUP)
BINDIR_ROOT = $(CURDIR)/bin
BINDIR      = $(BINDIR_ROOT)/$(BUILD_ID)
BENCH       = $(BINDIR)/benchmark

# Objects from the variant subdirectory
CASE_CPP_EXTRA ?=
CASE_OBJ    = $(BINDIR)/case_src.o
CUDA_OBJS   = $(foreach s,$(CASE_CUDA_EXTRA),$(BINDIR)/$(basename $(notdir $(s))).o)
CPP_OBJS    = $(foreach s,$(CASE_CPP_EXTRA), $(BINDIR)/$(basename $(notdir $(s))).o)
MAIN_SRC    ?= main.f90
MAIN_OBJ    = $(BINDIR)/main.o

ifeq ($(VARIANT),CUDA)
  ALL_OBJS = $(CASE_OBJ) $(CUDA_OBJS)
else ifneq ($(filter $(VARIANT),CPP CPP-OMP),)
  ALL_OBJS = $(CASE_OBJ) $(CPP_OBJS)
else
  ALL_OBJS = $(CASE_OBJ)
endif

# ---- Targets -----------------------------------------------
.PHONY: all clean clean-all test

all: $(BENCH)

$(BINDIR):
	mkdir -p $@

# Compile the variant's Fortran source (cvd.f90, cdu.f90, …)
$(CASE_OBJ): $(CASE)/$(VARIANT)/$(CASE_SRC) | $(BINDIR)
	$(FC) $(ALL_FFLAGS) $(DEFINES) -J $(BINDIR) -I$(BINDIR) -c $< -o $@

# Compile any extra CUDA sources (.cu files listed in CASE_CUDA_EXTRA)
# -I$(CURDIR)/common makes the shared common_functions.cuh visible to all cases
$(BINDIR)/%.o: $(CASE)/$(VARIANT)/%.cu | $(BINDIR)
	$(NVCC) $(NVCCFLAGS) -I$(CURDIR)/common -c $< -o $@

# Compile any extra C++ sources (.cpp files listed in CASE_CPP_EXTRA)
# -I$(CURDIR)/common makes the shared common_functions.cuh visible to all cases
$(BINDIR)/%.o: $(CASE)/$(VARIANT)/%.cpp | $(BINDIR)
	$(CXX) $(ALL_CXXFLAGS) -I$(CURDIR)/common -c $< -o $@

# Compile the benchmark driver (main.f90 in the CASE directory)
$(MAIN_OBJ): $(CASE)/$(MAIN_SRC) $(CASE_OBJ)
	$(FC) $(ALL_FFLAGS) $(DEFINES) -I$(BINDIR) -c $< -o $@

# Link everything
$(BENCH): $(MAIN_OBJ) $(ALL_OBJS)
	$(FC) $(FFLAGS) $(EXTRA_FFLAGS) -o $@ $^ $(VARIANT_LDFLAGS)

# Run correctness tests for all (or a specific) case
test:
	@python3 $(CURDIR)/run_tests.py $(CASE)

# Remove build artefacts for the current CASE/VARIANT/params combination
clean:
	rm -rf $(BINDIR)

# Wipe the entire bin/ tree (all cases, all variants)
clean-all:
	rm -rf $(BINDIR_ROOT)
