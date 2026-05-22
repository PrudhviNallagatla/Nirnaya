// tests/fixtures/enums.h
#pragma once

namespace data {

// Standard classic unscoped enum
enum StatusSeverity {
    SEVERITY_INFO = 0,
    SEVERITY_WARNING = 1,
    SEVERITY_ERROR = 10,
    SEVERITY_FATAL = 100
};

// Modern scoped enum with specific underlying type serialization
enum class StorageFormat : char {
    RAW_BINARY = 'B',
    COMPRESSED_ZSTD = 'Z',
    JSON_STRING = 'J'
};

} // namespace data