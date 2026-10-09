# GameCube / Wii → browser strategy

Status date: 2026-10-09.

## Current reality

The CPU/static-recomp side is strong and GXRuntime already carries a WebGPU/Dawn renderer substrate. The browser host is now split into small, mechanically proven work packages instead of one generic blocker.

- **DolRecomp** recompiles GameCube/Wii PowerPC DOL/REL code to C and also has an LLVM backend.
- **ModernGekko** is the ExpansionPak runtime for native recomp projects.
- **GXRuntime** is a game-agnostic runtime with PPC semantics, devices and a GX renderer. Its CPU semantics are validated against Dolphin's interpreter. Its vendored Aurora substrate already uses WebGPU via Chromium Dawn, and the public README reports full-game rendering through the current desktop/Aurora host.
- **RecompCore** is the accuracy/oracle route: statically recompiled code runs inside a Dolphin-derived runtime with interpreter fallback/lockstep.
- The pinned public GXRuntime tree still has no Emscripten/browser platform backend, but `labs/gcwii-web-surface/` now proves both the missing canvas surface primitive and a non-blocking browser adapter/device bootstrap with Emscripten 6.0.12 + `emdawnwebgpu`.

Aurora already expresses surface creation through a chained `wgpu::SurfaceDescriptor`. On native platforms it fills that chain from an SDL window. On the web, Emdawnwebgpu provides `wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`, so the browser path can preserve the renderer abstraction and substitute only the platform source.

The current Aurora `gpu.cpp` also requests `TimedWaitAny` and calls `WaitAny` for adapter/device creation. The browser probe demonstrates that this can instead be expressed as `RequestAdapter(AllowSpontaneous)` → `RequestDevice(AllowSpontaneous)` while the Emscripten event loop remains alive.

```text
GameCube/Wii DOL + RELs
        |
     DolRecomp
        |
 generated C / LLVM AOT
        |
 GXRuntime / ModernGekko core
        |
  +-----+------------------------+
  |                              |
Emscripten host              correctness oracle
  |                           RecompCore/Dolphin
WebAssembly
  |
existing GX WebGPU renderer
  |
canvas surface + async WebGPU bootstrap + WebAudio + Gamepad + storage
```

## Browser work packages

1. **Surface primitive — proven in isolation.** `reg_gcwii_web_surface` compiles Dawn-style `webgpu_cpp.h` with `--use-port=emdawnwebgpu` and creates a WebGPU surface for `#canvas`.
2. **Adapter/device bootstrap — proven in isolation.** `reg_gcwii_web_device` uses asynchronous WebGPU callbacks and explicitly contains no `WaitAny`/`TimedWaitAny` path.
3. Add an Emscripten Dawn provider in Aurora so web builds use Emdawnwebgpu rather than native Dawn packages/source.
4. Add the Emscripten canvas branch to `SetupWindowAndGetSurfaceDescriptor`.
5. Guard native-only Dawn instance setup (`dawn/native/DawnNative.h`, validation/platform hooks) and use the proven async bootstrap under Emscripten.
6. Prove the GXRuntime core and generated PPC code compile with Emscripten.
7. Define a Wasm-safe guest-memory model and keep the AOT path JIT-free.
8. Add browser input, audio and persistent memory-card/save storage.
9. If pthreads are needed, use a worker architecture and COOP/COEP isolation. The lab includes a local server with the required headers.
10. Validate PPC state and GX output against RecompCore/Dolphin before optimizing.

## Browser probes

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

CI pins Emscripten 6.0.12 and requires `.html`, `.js` and `.wasm` for both the surface and async device-bootstrap targets.

## Mechanical upstream gap check

```bash
python tools/gcwii_web_audit.py /path/to/GXRuntime --strict-foundation
```

The pinned **upstream GXRuntime** gap target still intentionally expects these rules to be missing:

```text
emscripten-build
browser-surface
cross-origin-isolation
```

The local probes do not change that claim: they prove generic adapters that can close those gaps; they do not claim the upstream GXRuntime tree already contains them.

`webgpu-renderer-core` is expected to pass because GXRuntime already has the Dawn/WebGPU renderer substrate. CI fails if the upstream missing expectations change so this repository can promote the route when upstream itself gains the browser host.
