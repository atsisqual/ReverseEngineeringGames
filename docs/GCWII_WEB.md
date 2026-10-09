# GameCube / Wii → browser strategy

Status date: 2026-10-09.

## Current reality

The CPU/static-recomp side is strong and GXRuntime already carries a WebGPU/Dawn renderer substrate. Browser bring-up is now decomposed into small, mechanically proven pieces rather than one generic blocker.

- **DolRecomp** recompiles GameCube/Wii PowerPC DOL/REL code to C and also has an LLVM backend.
- **ModernGekko** is the ExpansionPak runtime for native recomp projects.
- **GXRuntime** is a game-agnostic runtime with PPC semantics, devices and a GX renderer. Its CPU semantics are validated against Dolphin's interpreter. Its vendored Aurora substrate already uses WebGPU via Chromium Dawn.
- **RecompCore** remains the correctness/oracle route against Dolphin-derived behavior.
- The pinned public GXRuntime tree still has no Emscripten/browser platform backend, but `labs/gcwii-web-surface/` now proves the canvas surface, asynchronous adapter/device acquisition, and a synchronous-API bridge for the existing Aurora startup contract.

Aurora already creates surfaces through a chained `wgpu::SurfaceDescriptor`. Emdawnwebgpu provides `wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`, so the browser path can preserve the renderer abstraction and swap only the platform-specific source.

The current `aurora::initialize()` expects `webgpu::initialize()` to return a `bool` immediately. Native Dawn implements the request path with `TimedWaitAny`/`WaitAny`, while browser WebGPU is async-only. The browser probes now prove two usable alternatives:

- pure callback bootstrap with `CallbackMode::AllowSpontaneous`;
- a transitional synchronous C++ bridge using Asyncify + `emscripten_sleep(0)` to yield until callbacks complete.

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
canvas surface + WebGPU bootstrap + WebAudio + Gamepad + storage
```

## Browser work packages

1. **Surface primitive — proven.** `reg_gcwii_web_surface` compiles Dawn-style `webgpu_cpp.h` with `--use-port=emdawnwebgpu` and creates a WebGPU surface for `#canvas`.
2. **Async adapter/device bootstrap — proven.** `reg_gcwii_web_device` uses browser callbacks and contains no native future-wait path.
3. **Synchronous Aurora contract bridge — proven at compile/link level.** `reg_gcwii_web_syncbridge` links with `-sASYNCIFY=1`; `emscripten_sleep(0)` yields while adapter/device callbacks resolve, so a `bool initialize()`-style call can be retained during bring-up.
4. Add an Emscripten Dawn provider in Aurora so web builds use Emdawnwebgpu rather than native Dawn packages/source.
5. Add the Emscripten canvas branch to `SetupWindowAndGetSurfaceDescriptor`.
6. Guard native-only Dawn instance setup (`dawn/native/DawnNative.h`, validation/platform hooks) and transplant the sync bridge into the Emscripten `gpu.cpp` path.
7. Prove the patched GXRuntime/Aurora tree configures and then compiles with Emscripten.
8. Define a Wasm-safe guest-memory model and keep the AOT path JIT-free.
9. Add browser input, audio and persistent memory-card/save storage.
10. If pthreads are required, use COOP/COEP isolation and validate worker scheduling.
11. Validate PPC state and GX output against RecompCore/Dolphin before optimizing.

## Browser probes

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

CI pins Emscripten 6.0.12 and requires `.html`, `.js` and `.wasm` for all three targets: surface, async device bootstrap and synchronous Asyncify bridge.

Asyncify is intentionally a bring-up mechanism, not an architectural commitment. Once the real runtime boots, measure Wasm size/startup/runtime cost; if material, replace the bridge with an explicit asynchronous Aurora startup state machine using the already-proven callback flow.

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
