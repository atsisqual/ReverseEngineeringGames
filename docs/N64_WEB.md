# N64 browser strategy

Status date: 2026-10-09.

## What is now verified

- N64Recomp statically translates N64/MIPS functions to portable C and expects a
  runtime to provide platform behavior.
- N64ModernRuntime provides `ultramodern` + `librecomp`; projects supply
  platform callbacks and a renderer.
- **A true N64Recomp browser path exists in public code today.** The Ogre Battle
  64 recomp project has Emscripten runtime patches, Wasm pthreads, browser
  input/audio/persistence and a WebGL2 renderer prototype. Its browser build has
  reached real RSP display-list submission and renders the title sprite layer.
- That renderer is not yet universal or complete: current Ogre Battle 64 notes
  identify missing S2DEX2 support and incorrect parts of 3D/menu rendering.
- N64Wasm remains the practical emulator fallback for titles where a static
  recomp/decomp browser runtime is not yet economical.
- Emscripten SDK `latest` currently resolves to 6.0.12; this repo pins 6.0.12 in
  its own browser smoke CI.
- `recomp-kit` separately demonstrates static recompilation to a WebGPU browser
  host for older x86 Windows games and is useful architectural evidence.

## Decision tree

```text
N64 title
  |
  +-- matching decomp/source exists? -- yes --> Emscripten directly
  |                                          WebGL2/WebGPU + WebAudio + Gamepad
  |
  +-- symbols/ELF suitable for N64Recomp? -- yes --> N64Recomp -> C
  |                                                |
  |                                                +-> N64ModernRuntime
  |                                                     |
  |                                                     +-> Emscripten patches
  |                                                     +-> input/audio/storage
  |                                                     +-> game-specific GBI/RSP/RDP renderer work
  |
  +-- need browser execution now? -------- yes --> N64Wasm emulator fallback
```

## Reusable browser-runtime work packages

1. **Generated CPU code** — N64Recomp output must compile cleanly under the
   selected Emscripten/Clang revision without native executable-memory assumptions.
2. **Runtime memory** — replace native guard-page/mmap strategies with a Wasm-safe
   allocation model and choose a deliberate initial/maximum memory policy.
3. **Live recomp/JIT** — browsers do not allow the normal native executable-memory
   model; disable or stub live native recompilation for the web target.
4. **Threads** — map `std::thread`/runtime workers to Wasm pthreads and serve with
   COOP/COEP so `SharedArrayBuffer` is available.
5. **Input** — `labs/n64-web` contains a generic Gamepad-to-N64 mapping; real
   projects can wire equivalent callbacks/exports.
6. **Audio** — AudioWorklet is a proven approach; a stable shared Wasm heap avoids
   invalidating buffers handed to the worklet.
7. **Saving/ROM storage** — IDBFS/OPFS/WasmFS are viable. Ogre Battle 64 proves
   IDBFS persistence while keeping the user's ROM outside Git.
8. **Renderer** — this is now a *per-game/per-microcode engineering problem*, not
   an unknown feasibility problem. Ogre Battle 64's WebGL2 prototype is the
   concrete reference; coverage of F3DEX2/S2DEX2 and framebuffer/VI behavior must
   be measured for each title.
9. **Validation** — compare deterministic game-state milestones and native
   reference frames. A successful `.wasm` link is only the start.

## Tooling in this repository

- `labs/n64-web/` — small Emscripten/browser host probe.
- `tools/n64_web_audit.py` — static readiness audit for N64Recomp-style trees.
- `targets/ogre-battle-64/` — pinned real-game reference/orchestration that uses
  only a locally supplied ROM.
- `python portctl.py fetch n64-web` — core N64/web toolchain.
- `python portctl.py fetch n64-web-reference` — public projects worth studying.

## Agent rule

An agent must not call a static-recomp browser port complete because generated C
links to `.wasm` or because one display list renders. Completion requires the
actual target game's required microcodes/render paths plus input, audio, saving
and stable gameplay in a browser.
