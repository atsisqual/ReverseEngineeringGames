# GameCube / Wii → browser strategy

Status date: 2026-10-09.

## Current reality

The CPU/static-recomp side is strong and GXRuntime already carries a WebGPU/Dawn renderer substrate. The browser host is now split into smaller, measurable work packages instead of one generic blocker.

- **DolRecomp** recompiles GameCube/Wii PowerPC DOL/REL code to C and also has an LLVM backend.
- **ModernGekko** is the ExpansionPak runtime for native recomp projects.
- **GXRuntime** is a game-agnostic runtime with PPC semantics, devices and a GX renderer. Its CPU semantics are validated against Dolphin's interpreter. Its vendored Aurora substrate already uses WebGPU via Chromium Dawn, and the public README reports full-game rendering through the current desktop/Aurora host.
- **RecompCore** is the accuracy/oracle route: statically recompiled code runs inside a Dolphin-derived runtime with interpreter fallback/lockstep.
- The pinned public GXRuntime tree still has no Emscripten/browser platform backend, but `labs/gcwii-web-surface/` now proves the missing canvas surface primitive independently with Emscripten 6.0.12 + `emdawnwebgpu`.

That surface probe matters because Aurora already expresses surface creation through a chained `wgpu::SurfaceDescriptor`. On native platforms it fills that chain from an SDL window. On the web, Emdawnwebgpu provides `wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector`, so the browser path can keep the same WebGPU surface abstraction and substitute only the platform-specific source.

The recommended engineering path is therefore:

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
canvas surface + WebAudio + Gamepad + browser storage
```

## Browser work packages

1. **Surface primitive — proven in isolation.** `labs/gcwii-web-surface/` compiles Dawn-style `webgpu_cpp.h` with `--use-port=emdawnwebgpu` and creates a WebGPU surface for `#canvas`.
2. Add an Emscripten Dawn provider in Aurora so web builds use Emdawnwebgpu rather than native Dawn packages/source.
3. Add the Emscripten canvas branch to `SetupWindowAndGetSurfaceDescriptor`.
4. Guard native-only Dawn instance setup (`dawn/native/DawnNative.h`, backend validation/platform hooks).
5. Adapt GXRuntime/Aurora adapter/device acquisition where synchronous `WaitAny` semantics are not browser-safe.
6. Prove the headless/runtime core and generated PPC code compile with Emscripten.
7. Define a Wasm-safe guest-memory model and keep the AOT path JIT-free.
8. Add browser input, audio and persistent memory-card/save storage.
9. If pthreads are needed, use a worker architecture and COOP/COEP isolation. The surface lab includes a local server with the required headers.
10. Validate PPC state and GX output against RecompCore/Dolphin before optimizing.

## Surface probe

```bash
source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S labs/gcwii-web-surface -B build/gcwii-web-surface -G Ninja
cmake --build build/gcwii-web-surface
python labs/gcwii-web-surface/serve.py build/gcwii-web-surface
```

The CI version pins Emscripten 6.0.12 and requires the generated `.html`, `.js` and `.wasm` artifacts.

## Mechanical gap check

```bash
python tools/gcwii_web_audit.py /path/to/GXRuntime --strict-foundation
```

The pinned **upstream GXRuntime** gap target still intentionally expects these rules to be missing:

```text
emscripten-build
browser-surface
cross-origin-isolation
```

That is not contradicted by the local surface lab: the lab proves the adapter primitive that can close `browser-surface`; it does not claim the upstream GXRuntime tree already contains it.

`webgpu-renderer-core` is expected to pass: that detects the existing Dawn/WebGPU renderer substrate, not a completed browser target.

CI fails if the upstream missing expectations change. That is deliberate: when upstream gains a browser platform/surface backend, this repository should stop calling it a gap and promote it to a real browser reference target.
