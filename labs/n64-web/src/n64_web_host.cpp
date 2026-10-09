#include "reg/n64_web_host.hpp"

#include <algorithm>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#include <emscripten/html5.h>
#endif

namespace reg::n64web {
namespace {
constexpr double kDigitalThreshold = 0.5;

#ifdef __EMSCRIPTEN__
bool pressed(const EmscriptenGamepadEvent& pad, int button) {
    return button >= 0 && button < pad.numButtons && pad.digitalButton[button];
}

double axis(const EmscriptenGamepadEvent& pad, int index) {
    if (index < 0 || index >= pad.numAxes) {
        return 0.0;
    }
    return std::clamp(pad.axis[index], -1.0, 1.0);
}
#endif
} // namespace

ControllerState poll_controller(int index) {
    ControllerState out{};
#ifdef __EMSCRIPTEN__
    if (index < 0 || emscripten_sample_gamepad_data() != EMSCRIPTEN_RESULT_SUCCESS) {
        return out;
    }

    const int count = emscripten_get_num_gamepads();
    if (count <= index) {
        return out;
    }

    EmscriptenGamepadEvent pad{};
    if (emscripten_get_gamepad_status(index, &pad) != EMSCRIPTEN_RESULT_SUCCESS || !pad.connected) {
        return out;
    }

    out.connected = true;
    out.stick_x = static_cast<float>(axis(pad, 0));
    out.stick_y = static_cast<float>(-axis(pad, 1));

    if (pressed(pad, 0))  out.buttons |= Button::A;
    if (pressed(pad, 1))  out.buttons |= Button::B;
    if (pressed(pad, 6))  out.buttons |= Button::Z;
    if (pressed(pad, 9))  out.buttons |= Button::Start;
    if (pressed(pad, 12)) out.buttons |= Button::DUp;
    if (pressed(pad, 13)) out.buttons |= Button::DDown;
    if (pressed(pad, 14)) out.buttons |= Button::DLeft;
    if (pressed(pad, 15)) out.buttons |= Button::DRight;
    if (pressed(pad, 4))  out.buttons |= Button::L;
    if (pressed(pad, 5))  out.buttons |= Button::R;

    const double cx = axis(pad, 2);
    const double cy = axis(pad, 3);
    if (cx < -kDigitalThreshold) out.buttons |= Button::CLeft;
    if (cx >  kDigitalThreshold) out.buttons |= Button::CRight;
    if (cy < -kDigitalThreshold) out.buttons |= Button::CUp;
    if (cy >  kDigitalThreshold) out.buttons |= Button::CDown;
#endif
    return out;
}

bool set_rumble(int index, bool enabled) {
#ifdef __EMSCRIPTEN__
    return EM_ASM_INT({
        const getPads = navigator.getGamepads && navigator.getGamepads.bind(navigator);
        if (!getPads) return 0;
        const pad = getPads()[$0];
        if (!pad) return 0;
        const actuator = pad.vibrationActuator || (pad.hapticActuators && pad.hapticActuators[0]);
        if (!actuator || !actuator.playEffect) return 0;
        actuator.playEffect('dual-rumble', {
            duration: $1 ? 1000 : 0,
            strongMagnitude: $1 ? 1.0 : 0.0,
            weakMagnitude: $1 ? 1.0 : 0.0
        });
        return 1;
    }, index, enabled ? 1 : 0) != 0;
#else
    (void)index;
    (void)enabled;
    return false;
#endif
}

bool has_webgpu() {
#ifdef __EMSCRIPTEN__
    return EM_ASM_INT({ return typeof navigator !== 'undefined' && !!navigator.gpu; }) != 0;
#else
    return false;
#endif
}

bool is_cross_origin_isolated() {
#ifdef __EMSCRIPTEN__
    return EM_ASM_INT({ return typeof crossOriginIsolated !== 'undefined' && crossOriginIsolated; }) != 0;
#else
    return false;
#endif
}

void set_status_text(const char* text) {
#ifdef __EMSCRIPTEN__
    EM_ASM({
        let node = document.getElementById('reg-n64-status');
        if (!node) {
            node = document.createElement('pre');
            node.id = 'reg-n64-status';
            node.style.cssText = 'position:fixed;left:12px;top:12px;z-index:99999;padding:12px;background:#111;color:#0f0;font:14px monospace;white-space:pre-wrap';
            document.body.appendChild(node);
        }
        node.textContent = UTF8ToString($0);
    }, text);
#else
    (void)text;
#endif
}

} // namespace reg::n64web
