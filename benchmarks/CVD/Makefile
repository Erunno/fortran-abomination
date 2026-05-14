# ============================================================
# CVD Benchmark — top-level Makefile
#
# Usage:
#   make VARIANT=Fortran
#   make VARIANT=Fortran-OMP NX=128 NY=128 NZ=128 NITER=200 NWARMUP=10
#   make VARIANT=CUDA NX=128 NY=128 NZ=128 NITER=200 NWARMUP=10
#
# Variables:
#   VARIANT   — sub-directory to build (Fortran | Fortran-OMP | CUDA)
#   NX NY NZ  — interior grid dimensions  (default 64)
#   NITER     — timed iterations           (default 100)
#   NWARMUP   — warm-up iterations         (default 5)
#   FC        — Fortran compiler           (default gfortran)
#   FFLAGS    — base compiler flags        (default -O3)
#   EXTRA_FFLAGS — optional extra flags    (default empty)
#   CUDA_HOME — CUDA root                   (default /usr/local/cuda)
#   NVCC      — CUDA compiler               (default $(CUDA_HOME)/bin/nvcc)
# ============================================================

VARIANT  ?= Fortran
NX       ?= 64
NY       ?= 64
NZ       ?= 64
NITER    ?= 100
NWARMUP  ?= 5

# $(origin FC) == 'default' means make's built-in f77 — override it
ifeq ($(origin FC),default)
  FC = gfortran
else
  FC ?= gfortran
endif
FFLAGS   ?= -O3 -march=native -flto
EXTRA_FFLAGS ?=
CUDA_HOME ?= /usr/local/cuda
NVCC      ?= $(CUDA_HOME)/bin/nvcc

DEFINES   = -DVAR_NX=$(NX) -DVAR_NY=$(NY) -DVAR_NZ=$(NZ) \
            -DVAR_NITER=$(NITER) -DVAR_NWARMUP=$(NWARMUP)

# ---- Variant-specific flags --------------------------------
ifeq ($(VARIANT),Fortran-OMP)
  VARIANT_FFLAGS  = -fopenmp
  VARIANT_LDFLAGS = -fopenmp
	VARIANT_OBJS    = $(BINDIR)/cvd.o
else ifeq ($(VARIANT),CUDA)
	VARIANT_FFLAGS  =
	VARIANT_LDFLAGS = -L$(CUDA_HOME)/lib64 -lcudart -lstdc++
	VARIANT_OBJS    = $(BINDIR)/cvd.o $(BINDIR)/generated_code.o
else
  VARIANT_FFLAGS  =
  VARIANT_LDFLAGS =
	VARIANT_OBJS    = $(BINDIR)/cvd.o
endif

ALL_FFLAGS = $(FFLAGS) $(EXTRA_FFLAGS) $(VARIANT_FFLAGS) -cpp

BUILD_ID = $(VARIANT)_NX$(NX)_NY$(NY)_NZ$(NZ)_NITER$(NITER)_NWARMUP$(NWARMUP)
BINDIR_ROOT = $(CURDIR)/bin
BINDIR = $(BINDIR_ROOT)/$(BUILD_ID)
BENCH  = $(BINDIR)/benchmark_$(VARIANT)

# ---- Targets -----------------------------------------------
.PHONY: all clean build-variant

all: $(BENCH)

$(BINDIR):
	mkdir -p $@

# Delegate compilation of variant sources to the sub-makefile
build-variant: | $(BINDIR)
	$(MAKE) -C $(VARIANT) \
	    FC="$(FC)" \
	    NVCC="$(NVCC)" \
	    FFLAGS="$(FFLAGS) $(EXTRA_FFLAGS) $(VARIANT_FFLAGS)" \
	    DEFINES="$(DEFINES)" \
	    BINDIR="$(BINDIR)"

# Compile main — .mod file lives in BINDIR (written by the sub-make)
$(BINDIR)/main.o: main.f90 | build-variant
	$(FC) $(ALL_FFLAGS) $(DEFINES) -I$(BINDIR) -c main.f90 -o $(BINDIR)/main.o

# Link
$(BENCH): $(BINDIR)/main.o | build-variant
	$(FC) $(FFLAGS) $(EXTRA_FFLAGS) -o $(BENCH) $(BINDIR)/main.o $(VARIANT_OBJS) $(VARIANT_LDFLAGS)

clean:
	rm -rf $(BINDIR_ROOT)
