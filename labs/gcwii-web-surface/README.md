# GameCube/Wii WebGPU browser-surface spike

This lab isolates the browser-specific WebGPU primitives needed by
GXRuntime/Aurora before changing the runtime itself.

The pinned GXRuntime code creates a WebGPU surface through
`SetupWindowAndGetSurfaceDescriptor(SDL_Window*)` and its public startup path
expects `webgpu::initialize(...)` to return a `bool` synchronously. Native Dawn
satisfies that today with `TimedWaitAny`/`WaitAny`; browser WebGPU resolves
adapter/device requests asynchronously.

Modern Emscripten provides Dawn-style `webgpu.h` and `webgpu_cpp.h` through the
`emdawnwebgpu` port. The probes here prove the browser pieces independently:

1. `reg_gcwii_web_surface` creates a WebGPU surface from HTML canvas `#canvas`
   via `wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`.
2. `reg_gcwii_web_device` requests adapter and device asynchronously with
   `wgpu::CallbackMode::AllowSpontaneous`, without the native future-wait APIs.
3. `reg_gcwii_web_syncbridge` preserves a synchronous C++ initialization
   contract using `-sASYNCIFY=1` and `emscripten_sleep(0)` to yield to the JS
   event loop until those same callbacks complete.

## Build

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

Browser entry points:

```text
http://127.0.0.1:8932/reg_gcwii_web_surface.html
http://127.0.0.1:8932/reg_gcwii_web_device.html
http://127.0.0.1:8932/reg_gcwii_web_syncbridge.html
```

## What this proves

- Emscripten can compile Dawn-style C++ WebGPU bindings without native Dawn.
- A browser canvas can use the same chained surface-descriptor model Aurora
  already consumes.
- Adapter/device creation works through browser-event-loop callbacks.
- Aurora's current synchronous initialization shape can be retained initially:
  Asyncify unwinds during `emscripten_sleep(0)`, allowing WebGPU callbacks to
  run before the C++ call resumes.
- A local host can provide COOP/COEP headers for later pthread/SharedArrayBuffer
  work.

## Why Asyncify is a bridge, not the end state

The sync bridge avoids a broad Aurora API rewrite while bringing up the first
browser build. Asyncify can increase Wasm size and add overhead around instrumented
call paths, so it should be measured after the real runtime boots. If the cost is
material, the proven callback flow can later replace synchronous initialization
with an explicit async startup state machine.

## What this does not prove yet

- GXRuntime itself builds under Emscripten.
- Aurora's Dawn provider selects `emdawnwebgpu` on the web.
- `BackendBinding.cpp` contains the canvas branch.
- Native Dawn headers/setup are fully excluded from the Emscripten build.
- The real `gpu.cpp` uses the sync bridge.
- SDL/input/audio/storage are browser-integrated.
- A GameCube/Wii title reaches first frame.

The next step is therefore no longer another API experiment: apply these three
proven primitives to the pinned GXRuntime/Aurora tree and make that patched tree
configure/compile under Emscripten.
