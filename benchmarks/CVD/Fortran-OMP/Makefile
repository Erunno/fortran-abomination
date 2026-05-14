# ============================================================
# CVD Fortran-OMP variant — sub-makefile
# OpenMP is enabled here; the top-level Makefile also passes
# -fopenmp in FFLAGS so this file stays self-contained.
# ============================================================

ifeq ($(origin FC),default)
  FC = gfortran
else
  FC ?= gfortran
endif
FFLAGS  ?= -O2 -fopenmp
DEFINES ?=

SRCS = cvd.f90
BINDIR ?= .
OBJS    = $(BINDIR)/cvd.o

.PHONY: all clean

all: $(OBJS)

$(BINDIR)/cvd.o: cvd.f90
	$(FC) $(FFLAGS) $(DEFINES) -cpp -J $(BINDIR) -c $< -o $@

clean:
	rm -f $(BINDIR)/cvd.o $(BINDIR)/momentumadvection.mod
