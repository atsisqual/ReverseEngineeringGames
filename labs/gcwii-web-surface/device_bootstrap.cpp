#include <cstdio>
#include <utility>

#include <emscripten/emscripten.h>
#include <webgpu/webgpu_cpp.h>

#ifndef __EMSCRIPTEN__
#error "gcwii web device bootstrap requires Emscripten"
#endif

namespace {

enum class BootstrapState {
  WaitingAdapter,
  WaitingDevice,
  Ready,
  Failed,
};

BootstrapState g_state = BootstrapState::WaitingAdapter;
wgpu::Instance g_instance;
wgpu::Surface g_surface;
wgpu::Adapter g_adapter;
wgpu::Device g_device;

void request_device() {
  wgpu::DeviceDescriptor descriptor{};
  g_state = BootstrapState::WaitingDevice;
  g_adapter.RequestDevice(
      &descriptor, wgpu::CallbackMode::AllowSpontaneous,
      [](wgpu::RequestDeviceStatus status, wgpu::Device device, wgpu::StringView message) {
        (void)message;
        if (status != wgpu::RequestDeviceStatus::Success) {
          std::fputs("gcwii-web-device: device request failed\n", stderr);
          g_state = BootstrapState::Failed;
          return;
        }
        g_device = std::move(device);
        g_state = BootstrapState::Ready;
      });
}

void tick() {
  if (g_state == BootstrapState::Ready) {
    std::puts("gcwii-web-device: adapter/device bootstrap ready");
    emscripten_cancel_main_loop();
  } else if (g_state == BootstrapState::Failed) {
    emscripten_cancel_main_loop();
  }
}

}  // namespace

int main() {
  wgpu::InstanceDescriptor instance_descriptor{};
  g_instance = wgpu::CreateInstance(&instance_descriptor);
  if (!g_instance) {
    std::fputs("gcwii-web-device: failed to create WebGPU instance\n", stderr);
    return 1;
  }

  wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector canvas_source{};
  canvas_source.selector = "#canvas";
  wgpu::SurfaceDescriptor surface_descriptor{};
  surface_descriptor.nextInChain = &canvas_source;
  surface_descriptor.label = "GXRuntime async browser bootstrap";
  g_surface = g_instance.CreateSurface(&surface_descriptor);
  if (!g_surface) {
    std::fputs("gcwii-web-device: failed to create canvas surface\n", stderr);
    return 2;
  }

  wgpu::RequestAdapterOptions options{};
  options.powerPreference = wgpu::PowerPreference::HighPerformance;
  options.compatibleSurface = g_surface;

  g_instance.RequestAdapter(
      &options, wgpu::CallbackMode::AllowSpontaneous,
      [](wgpu::RequestAdapterStatus status, wgpu::Adapter adapter, wgpu::StringView message) {
        (void)message;
        if (status != wgpu::RequestAdapterStatus::Success) {
          std::fputs("gcwii-web-device: adapter request failed\n", stderr);
          g_state = BootstrapState::Failed;
          return;
        }
        g_adapter = std::move(adapter);
        request_device();
      });

  // Browser WebGPU resolves adapter/device requests asynchronously. Keep the JS
  // event loop alive; deliberately do not use Dawn's native TimedWaitAny/WaitAny.
  emscripten_set_main_loop(tick, 0, 1);
  return 0;
}
