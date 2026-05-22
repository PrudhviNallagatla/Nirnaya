// tests/fixtures/cpp_class.h
#pragma once

#include <string>

namespace network {

class ConnectionManager {
public:
    ConnectionManager();
    virtual ~ConnectionManager() = default;

    // ABI tracking targets
    virtual bool connect(const std::string& host, int32_t port);
    void disconnect() noexcept;
    
    // Const and static configurations
    bool is_connected() const;
    static int32_t get_active_connection_count();

private:
    int32_t m_socket_fd;
    bool    m_is_authenticated;
    double  m_timeout_seconds;
};

// Global free function within the same namespace to verify non-member processing
void broadcast_payload(const std::string& payload, int32_t channel_flags);

} // namespace network