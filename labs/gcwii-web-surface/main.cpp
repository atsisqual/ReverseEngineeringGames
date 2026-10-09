#include <cstdio>

#include <webgpu/webgpu_cpp.h>

#ifndef __EMSCRIPTEN__
#error "gcwii web surface probe requires Emscripten"
#endif

int main() {
  wgpu::InstanceDescriptor instance_descriptor{};
  wgpu::Instance instance = wgpu::CreateInstance(&instance_descriptor);
  if (!instance) {
    std::fputs("failed to create WebGPU instance\n", stderr);
    return 1;
  }

  // This is the browser equivalent of GXRuntime/Aurora's native
  // SetupWindowAndGetSurfaceDescriptor(SDL_Window*) path.
  wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector canvas_source{};
  canvas_source.selector = "#canvas";

  wgpu::SurfaceDescriptor surface_descriptor{};
  surface_descriptor.nextInChain = &canvas_source;
  surface_descriptor.label = "GXRuntime browser surface probe";

  wgpu::Surface surface = instance.CreateSurface(&surface_descriptor);
  if (!surface) {
    std::fputs("failed to create WebGPU canvas surface\n", stderr);
    return 2;
  }

  std::puts("gcwii-web-surface: canvas WebGPU surface created");
  return 0;
}
