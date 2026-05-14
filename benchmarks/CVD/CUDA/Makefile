# ============================================================
# CVD CUDA variant - sub-makefile
# Builds Fortran module wrapper + generated CUDA object.
# ============================================================

ifeq ($(origin FC),default)
  FC = gfortran
else
  FC ?= gfortran
endif

CUDA_HOME ?= /usr/local/cuda
NVCC ?= $(CUDA_HOME)/bin/nvcc

FFLAGS    ?= -O3
DEFINES   ?=
NVCCFLAGS ?= -O3
CUDA_ARCH ?=

ifneq ($(CUDA_ARCH),)
  NVCCFLAGS += -arch=$(CUDA_ARCH)
endif

BINDIR ?= .
OBJS   = $(BINDIR)/cvd.o $(BINDIR)/generated_code.o

.PHONY: all clean

all: $(OBJS)

$(BINDIR)/cvd.o: cvd.f90
	$(FC) $(FFLAGS) $(DEFINES) -cpp -J $(BINDIR) -c $< -o $@

$(BINDIR)/generated_code.o: generated_code.cu
	$(NVCC) $(NVCCFLAGS) -c $< -o $@

clean:
	rm -f $(BINDIR)/cvd.o $(BINDIR)/generated_code.o $(BINDIR)/momentumadvection.mod
