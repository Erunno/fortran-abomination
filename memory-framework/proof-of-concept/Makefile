# Define compilers
CXX = g++
FC = gfortran

# Define compiler flags
CXXFLAGS = -Wall -O3 -std=c++20
FCFLAGS = -Wall -O3
LDFLAGS = -lstdc++

# Output executable name
TARGET = pure_fortran_app

# Object files to build
OBJS = managed_mem.o main.o

ARGS ?= 1

# Default target runs when you just type 'make'
all: $(TARGET)

# Link the object files to create the final executable
$(TARGET): $(OBJS)
	$(FC) $(OBJS) -o $(TARGET) $(LDFLAGS)

# Compile the C++ file
managed_mem.o: managed_mem.cpp
	$(CXX) $(CXXFLAGS) -c managed_mem.cpp -o managed_mem.o

# Compile the Fortran file
main.o: main.f90
	$(FC) $(FCFLAGS) -c main.f90 -o main.o

# Clean up build files
clean:
	rm -f $(OBJS) $(TARGET)

# Run the application with arguments
run: $(TARGET) 
	./$(TARGET) $(ARGS)

test: $(TARGET)
	./$(TARGET) 1
	@echo ""
	./$(TARGET) 2
	@echo ""
	./$(TARGET) 3
	@echo ""
	./$(TARGET) 4