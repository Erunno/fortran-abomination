# ============================================================
# CVD Fortran variant — sub-makefile
# Called by the top-level Makefile; may also be invoked
# standalone for quick development builds.
# ============================================================

ifeq ($(origin FC),default)
  FC = gfortran
else
  FC ?= gfortran
endif
FFLAGS  ?= -O2
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
