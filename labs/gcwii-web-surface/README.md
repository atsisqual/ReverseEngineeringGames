# GameCube/Wii WebGPU browser-surface spike

This lab isolates the browser-specific WebGPU primitives needed by
GXRuntime/Aurora before changing the runtime itself.

The pinned GXRuntime code creates a WebGPU surface by asking
`SetupWindowAndGetSurfaceDescriptor(SDL_Window*)` for a native chained surface
descriptor. That helper supports Cocoa, Android, Win32, Wayland and X11, but no
Emscripten/browser canvas path. Its GPU bootstrap also requests
`TimedWaitAny` and synchronously waits for adapter/device futures.

Modern Emscripten provides Dawn-style `webgpu.h` and `webgpu_cpp.h` through the
`emdawnwebgpu` port. The probes here use those same C++ bindings to prove two
pieces independently:

1. `reg_gcwii_web_surface` creates a WebGPU surface from HTML canvas `#canvas`
   via `wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`.
2. `reg_gcwii_web_device` requests the adapter and device asynchronously using
   `wgpu::CallbackMode::AllowSpontaneous`, with no `WaitAny`/`TimedWaitAny`.

## Build

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

Then open either probe in a browser with WebGPU enabled:

```text
http://127.0.0.1:8932/reg_gcwii_web_surface.html
http://127.0.0.1:8932/reg_gcwii_web_device.html
```

## What this proves

- Emscripten can compile Dawn-style C++ WebGPU bindings without native Dawn.
- A browser canvas can be represented as a WebGPU surface using the same chained
  descriptor model GXRuntime already consumes.
- Adapter/device creation can be expressed as a browser-event-loop callback
  chain instead of blocking on Dawn's native `WaitAny` path.
- A local host can provide the COOP/COEP headers required later if GXRuntime uses
  Wasm pthreads/SharedArrayBuffer.

## What this does not prove yet

- GXRuntime itself builds under Emscripten.
- Aurora's native Dawn provider has been replaced by `emdawnwebgpu`.
- `gpu.cpp` has been split so native Dawn keeps `TimedWaitAny` while the browser
  path uses the proven asynchronous callback bootstrap.
- SDL/input/audio/storage are browser-integrated.
- A GameCube/Wii title reaches first frame.

The next integration patch can now be narrow and evidence-driven: add an
Emscripten Dawn provider, add the canvas branch to `BackendBinding.cpp`, guard
native Dawn setup, and transplant the asynchronous adapter/device bootstrap into
the Emscripten branch of Aurora before moving on to runtime memory and I/O.
