#include "reg/n64_web_host.hpp"

#include <cstdio>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#endif

namespace {
void tick() {
    const auto pad = reg::n64web::poll_controller(0);
    char buffer[512];
    std::snprintf(
        buffer,
        sizeof(buffer),
        "ReverseEngineeringGames N64 web host probe\n"
        "WebGPU: %s\n"
        "crossOriginIsolated: %s\n"
        "controller 0: %s\n"
        "buttons: 0x%04X\n"
        "stick: %.3f, %.3f\n\n"
        "Press a controller button if the browser has not exposed it yet.",
        reg::n64web::has_webgpu() ? "yes" : "no",
        reg::n64web::is_cross_origin_isolated() ? "yes" : "no",
        pad.connected ? "connected" : "not connected",
        static_cast<unsigned>(pad.buttons),
        static_cast<double>(pad.stick_x),
        static_cast<double>(pad.stick_y));
    reg::n64web::set_status_text(buffer);
}
} // namespace

int main() {
#ifdef __EMSCRIPTEN__
    tick();
    emscripten_set_main_loop(tick, 0, true);
#else
    const auto pad = reg::n64web::poll_controller(0);
    std::printf("native syntax/smoke build OK; controller connected=%d\n", pad.connected ? 1 : 0);
#endif
    return 0;
}
