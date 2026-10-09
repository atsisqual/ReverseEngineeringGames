#pragma once

#include <cstdint>

namespace reg::n64web {

enum Button : std::uint16_t {
    A       = 0x8000,
    B       = 0x4000,
    Z       = 0x2000,
    Start   = 0x1000,
    DUp     = 0x0800,
    DDown   = 0x0400,
    DLeft   = 0x0200,
    DRight  = 0x0100,
    L       = 0x0020,
    R       = 0x0010,
    CUp     = 0x0008,
    CDown   = 0x0004,
    CLeft   = 0x0002,
    CRight  = 0x0001,
};

struct ControllerState {
    bool connected = false;
    std::uint16_t buttons = 0;
    float stick_x = 0.0F;
    float stick_y = 0.0F;
};

ControllerState poll_controller(int index = 0);
bool set_rumble(int index, bool enabled);
bool has_webgpu();
bool is_cross_origin_isolated();
void set_status_text(const char* text);

} // namespace reg::n64web
