# ============================================================
# variants.mk — per-variant compiler flags and linker flags
# Included by the top-level Makefile after defaults.mk.
# Defines: VARIANT_FFLAGS, VARIANT_LDFLAGS
# ============================================================

ifeq ($(VARIANT),Fortran-OMP)
  VARIANT_FFLAGS  = -fopenmp
  VARIANT_LDFLAGS = -fopenmp

else ifeq ($(VARIANT),CUDA)
  VARIANT_FFLAGS  =
  VARIANT_LDFLAGS = -L$(CUDA_HOME)/lib64 -lcudart -lstdc++
  ifneq ($(CUDA_ARCH),)
    NVCCFLAGS += -arch=$(CUDA_ARCH)
  endif

else
  # Plain Fortran (no extra flags needed)
  VARIANT_FFLAGS  =
  VARIANT_LDFLAGS =
endif
