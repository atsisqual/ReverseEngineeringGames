# GameCube/Wii WebGPU browser-surface spike

This lab proves the browser surface primitive that GXRuntime/Aurora is currently
missing in its native-only window binding.

The pinned GXRuntime code creates a WebGPU surface by asking
`SetupWindowAndGetSurfaceDescriptor(SDL_Window*)` for a native chained surface
descriptor. That helper supports Cocoa, Android, Win32, Wayland and X11, but no
Emscripten/browser canvas path.

Modern Emscripten provides Dawn-style `webgpu.h` and `webgpu_cpp.h` through the
`emdawnwebgpu` port. This probe compiles those exact C++ bindings to Wasm and
creates a surface from the HTML canvas selector `#canvas` using
`wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`.

## Build

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

Then open `http://127.0.0.1:8932/reg_gcwii_web_surface.html` in a browser with
WebGPU enabled.

## What this proves

- Emscripten can compile Dawn-style C++ WebGPU bindings without native Dawn.
- A browser canvas can be represented as a WebGPU surface using the same chained
  descriptor model GXRuntime already consumes.
- A local host can provide the COOP/COEP headers required later if GXRuntime uses
  Wasm pthreads/SharedArrayBuffer.

## What this does not prove yet

- GXRuntime itself builds under Emscripten.
- Aurora's native Dawn provider has been replaced by `emdawnwebgpu`.
- `gpu.cpp`'s native-Dawn instance setup and synchronous `WaitAny` adapter/device
  acquisition are browser-safe.
- SDL/input/audio/storage are browser-integrated.
- A GameCube/Wii title reaches first frame.

The next integration patch should therefore be narrow: add an Emscripten Dawn
provider, add the canvas branch to `BackendBinding.cpp`, guard native Dawn setup,
and adapt adapter/device acquisition to the browser callback model before moving
on to input/audio/storage.
