// tests/fixtures/simple_struct.h
#pragma once

#include <stdint.h>

namespace core {

/**
 * @brief Simple flat layout with explicit padding bytes to verify
 * that bit offsets match real compiler alignments.
 */
struct SimpleStruct {
    uint8_t  id;         // Offset: 0 bits
    // uint32_t sneaky_rogue_field;  // this is added for testing ----- Offset: 8 bits
    // 3 bytes padding injected automatically by compiler alignment rules
    int32_t  value;      // Offset: 40 bits
    double   factor;     // Offset: 64 bits
    bool     is_active;  // Offset: 128 bits
};

// Test simple global alias extraction
typedef int32_t SystemHandle;
using NetworkToken = uint64_t;

} // namespace core