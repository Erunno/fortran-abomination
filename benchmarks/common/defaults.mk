# ============================================================
# defaults.mk — shared default values for all benchmarks
# Included by the top-level Makefile; override any variable
# on the command line:  make CASE=CVD NX=256 FC=ifort
# ============================================================

# ---- Benchmark grid / iteration parameters -----------------
NX      ?= 64
NY      ?= 64
NZ      ?= 64
NITER   ?= 100
NWARMUP ?= 5

# ---- Fortran compiler & flags ------------------------------
# Guard against make's built-in FC=f77 default
ifeq ($(origin FC),default)
  FC = gfortran
else
  FC ?= gfortran
endif
FFLAGS       ?= -O3 -march=native -flto
EXTRA_FFLAGS ?=

# ---- C++ compiler & flags ---------------------------------
CXX          ?= g++
CXXFLAGS     ?= -O3 -march=native
EXTRA_CXXFLAGS ?=

# ---- CUDA compiler & flags ---------------------------------
CUDA_HOME  ?= /usr/local/cuda
NVCC       ?= $(CUDA_HOME)/bin/nvcc
NVCCFLAGS  ?= -O3
CUDA_ARCH  ?=
