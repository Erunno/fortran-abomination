# ============================================================
# variants.mk — per-variant compiler flags and linker flags
# Included by the top-level Makefile after defaults.mk.
# Defines: VARIANT_FFLAGS, VARIANT_LDFLAGS
# ============================================================

ifeq ($(VARIANT),Fortran-OMP)
  VARIANT_FFLAGS   = -fopenmp
  VARIANT_LDFLAGS  = -fopenmp
  VARIANT_CXXFLAGS =

else ifeq ($(VARIANT),CUDA)
  VARIANT_FFLAGS   =
  VARIANT_LDFLAGS  = -L$(CUDA_HOME)/lib64 -lcudart -lstdc++
  VARIANT_CXXFLAGS =
  ifneq ($(CUDA_ARCH),)
    NVCCFLAGS += -arch=$(CUDA_ARCH)
  endif

else ifeq ($(VARIANT),CPP)
  VARIANT_FFLAGS   =
  VARIANT_LDFLAGS  = -static-libstdc++
  VARIANT_CXXFLAGS =

else ifeq ($(VARIANT),CPP-OMP)
  VARIANT_FFLAGS   = -fopenmp
  VARIANT_LDFLAGS  = -static-libstdc++ -fopenmp
  VARIANT_CXXFLAGS = -fopenmp

else
  # Plain Fortran (no extra flags needed)
  VARIANT_FFLAGS   =
  VARIANT_LDFLAGS  =
  VARIANT_CXXFLAGS =
endif
