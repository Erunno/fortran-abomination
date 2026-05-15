# ============================================================
# standalone.mk — convenience wrapper for building a single
# variant from inside its own directory.
#
# The including Makefile sets CASE and VARIANT, then includes
# this file.  Example (CVD/Fortran/Makefile):
#
#   CASE    = CVD
#   VARIANT = Fortran
#   include ../../common/standalone.mk
#
# Any extra make variables (NX, FC, FFLAGS, …) can still be
# passed on the command line and are forwarded automatically.
# ============================================================

# Resolve the benchmarks/ root relative to this file's location
BENCHMARKS_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))..)

.PHONY: all clean

all:
	$(MAKE) -C $(BENCHMARKS_DIR) CASE=$(CASE) VARIANT=$(VARIANT)

clean:
	$(MAKE) -C $(BENCHMARKS_DIR) clean CASE=$(CASE) VARIANT=$(VARIANT)
