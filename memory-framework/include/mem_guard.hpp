#include <vector>
#include <cuda_runtime.h>

namespace mem_guard
{

struct BufferRecord {
    void* host_ptr;
    void* gpu_ptr;
    size_t size_in_bytes;

    bool is_access_to_mem(void* ptr) const {
        return (ptr >= host_ptr) && (ptr < static_cast<char*>(host_ptr) + size_in_bytes);
    }
};


class GpuMemGuard {
  public:
    GpuMemGuard() = default;
    ~GpuMemGuard() = default;
    
    template <typename ItemType>
    bool is_on_gpu(const ItemType* buffer) const {
        auto record = find_buffer_record(buffer);
        return (record != nullptr);
    }

    template <typename ItemType>
    void move_to_gpu(const ItemType* buffer, size_t num_items) {
        cudaMalloc(&gpu_ptr, num_items * sizeof(ItemType));
    }

    template <typename ItemType>
    void move_to_host(const ItemType* buffer) {
        move_mem<cudaMemcpyDeviceToHost>(buffer);
    }

    template <typename ItemType>
    void move_to_gpu(const ItemType* buffer) {
        move_mem<cudaMemcpyHostToDevice>(buffer);
    }

    template <typename ItemType>
    ItemType* get_gpu_address(const ItemType* item) const {
        // Implementation to get the GPU address of the item
    }

    template <typename ItemType>
    void protect_from_read_writes(const ItemType* item) {
        
    }

    
    template <typename ItemType>
    void protect_from_writes(const ItemType* item) {
        // Implementation to protect the item from write operations
    }

    template <typename ItemType>
    void unprotect(const ItemType* item) {
        // Implementation to unprotect the item from read/write operations
    }

  private:
    std::vector<BufferRecord> buffer_records;

    BufferRecord* find_buffer_record(const void* ptr) const {
        for (const auto& record : buffer_records) {
            if (record.is_access_to_mem(const_cast<void*>(ptr))) {
                return &record;
            }
        }
        return nullptr;
    }

    template <auto mem_direction>
    void move_mem(const void* buffer) {
        auto record = find_buffer_record(buffer);

        if (record == nullptr) {
            throw std::runtime_error("Buffer not found in records");
        }
     
        if constexpr (mem_direction == cudaMemcpyHostToDevice) {
            cudaMemcpy(record->gpu_ptr, record->host_ptr, record->size_in_bytes, cudaMemcpyHostToDevice);
        } else if constexpr (mem_direction == cudaMemcpyDeviceToHost) {
            cudaMemcpy(record->host_ptr, record->gpu_ptr, record->size_in_bytes, cudaMemcpyDeviceToHost);
        }
    }
};

GpuMemGuard gpu_mem_guard;

}