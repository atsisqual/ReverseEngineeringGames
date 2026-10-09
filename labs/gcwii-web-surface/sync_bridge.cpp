#include <cstdio>
#include <utility>

#include <emscripten/emscripten.h>
#include <webgpu/webgpu_cpp.h>

#ifndef __EMSCRIPTEN__
#error "gcwii sync WebGPU bridge requires Emscripten"
#endif

namespace {

struct AdapterResult {
  bool done = false;
  wgpu::RequestAdapterStatus status = wgpu::RequestAdapterStatus::CallbackCancelled;
  wgpu::Adapter adapter;
};

struct DeviceResult {
  bool done = false;
  wgpu::RequestDeviceStatus status = wgpu::RequestDeviceStatus::CallbackCancelled;
  wgpu::Device device;
};

AdapterResult g_adapter_result;
DeviceResult g_device_result;

bool request_adapter_sync(const wgpu::Instance& instance, const wgpu::Surface& surface, wgpu::Adapter& out) {
  g_adapter_result = {};
  wgpu::RequestAdapterOptions options{};
  options.powerPreference = wgpu::PowerPreference::HighPerformance;
  options.compatibleSurface = surface;

  instance.RequestAdapter(
      &options, wgpu::CallbackMode::AllowSpontaneous,
      [](wgpu::RequestAdapterStatus status, wgpu::Adapter adapter, wgpu::StringView message) {
        (void)message;
        g_adapter_result.status = status;
        if (status == wgpu::RequestAdapterStatus::Success) {
          g_adapter_result.adapter = std::move(adapter);
        }
        g_adapter_result.done = true;
      });

  while (!g_adapter_result.done) {
    emscripten_sleep(0);
  }
  if (g_adapter_result.status != wgpu::RequestAdapterStatus::Success || !g_adapter_result.adapter) {
    return false;
  }
  out = std::move(g_adapter_result.adapter);
  return true;
}

bool request_device_sync(const wgpu::Adapter& adapter, wgpu::Device& out) {
  g_device_result = {};
  wgpu::DeviceDescriptor descriptor{};
  adapter.RequestDevice(
      &descriptor, wgpu::CallbackMode::AllowSpontaneous,
      [](wgpu::RequestDeviceStatus status, wgpu::Device device, wgpu::StringView message) {
        (void)message;
        g_device_result.status = status;
        if (status == wgpu::RequestDeviceStatus::Success) {
          g_device_result.device = std::move(device);
        }
        g_device_result.done = true;
      });

  while (!g_device_result.done) {
    emscripten_sleep(0);
  }
  if (g_device_result.status != wgpu::RequestDeviceStatus::Success || !g_device_result.device) {
    return false;
  }
  out = std::move(g_device_result.device);
  return true;
}

bool initialize_sync(wgpu::Instance& instance, wgpu::Surface& surface, wgpu::Adapter& adapter, wgpu::Device& device) {
  wgpu::InstanceDescriptor instance_descriptor{};
  instance = wgpu::CreateInstance(&instance_descriptor);
  if (!instance) {
    return false;
  }

  wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector canvas_source{};
  canvas_source.selector = "#canvas";
  wgpu::SurfaceDescriptor surface_descriptor{};
  surface_descriptor.nextInChain = &canvas_source;
  surface_descriptor.label = "GXRuntime synchronous browser bridge";
  surface = instance.CreateSurface(&surface_descriptor);
  if (!surface) {
    return false;
  }

  return request_adapter_sync(instance, surface, adapter) && request_device_sync(adapter, device);
}

}  // namespace

int main() {
  wgpu::Instance instance;
  wgpu::Surface surface;
  wgpu::Adapter adapter;
  wgpu::Device device;
  if (!initialize_sync(instance, surface, adapter, device)) {
    std::fputs("gcwii-web-syncbridge: initialization failed\n", stderr);
    return 1;
  }
  std::puts("gcwii-web-syncbridge: synchronous C++ contract preserved");
  return 0;
}
