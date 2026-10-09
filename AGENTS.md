# Agent instructions

This repository is designed to be used by coding agents as a reverse-engineering/porting workbench.

## Goal

Move a game toward a browser build through the safest viable path:

1. identify the original platform and executable format;
2. inventory existing decomp/recomp/runtime projects;
3. establish a deterministic native baseline;
4. choose source-port, static-recomp or emulator-core route;
5. make the CPU/runtime portable;
6. compile to WebAssembly;
7. adapt graphics/audio/input/filesystem/networking to browser APIs;
8. prove behavior with automated tests and reproducible hashes/traces.

Never describe an experimental route as working unless the build and browser test prove it.

## Hard rules

- Do not commit ROMs, ISOs, keys, firmware, extracted commercial assets or proprietary SDK/compiler binaries.
- Do not add download automation for copyrighted game content.
- Do not bypass DRM, authentication, copy protection or platform security.
- User-provided original inputs belong in ignored local directories.
- Prefer upstream open-source tooling and preserve upstream licenses.
- Keep third-party tools in `.tools/`; do not copy their source into this repo.
- Record exact upstream commit SHAs in each real port workspace once the route stabilizes.
- Make small, verifiable changes. A compiler success is not equivalent to behavioral correctness.
- For matching decompilation, use the project's verifier (`objdiff`, `reccmp`, project diff scripts) as ground truth.

## Route selection

### Existing portable source/decomp
Use Emscripten first. Replace platform APIs incrementally and keep the native build working.

### N64
Try N64Recomp when suitable metadata exists. Treat its generated C as CPU-side output, not as a complete web port. Audit the runtime/renderer for browser-hostile assumptions before compiling with Emscripten.

### GameCube / Wii
Use `decomp-toolkit` + `objdiff` for matching-decomp work, or DolRecomp for CPU static recompilation. DolRecomp explicitly leaves graphics/audio/input/platform integration to the host runtime, so browser work generally lives in that runtime layer.

### Old Windows x86
When source is unavailable, use matching decompilation where feasible. `reccmp` is especially useful for older MSVC 32-bit x86 projects. Once enough portable C/C++ exists, target Emscripten.

### Unsupported binary/platform
Do not invent a static-recompiler path. Evaluate an open emulator core that already runs portably, then compile the emulator/core to Wasm if licensing permits.

## Web build defaults

Prefer:

- Emscripten + CMake/Ninja;
- SDL for portable window/input/audio abstraction when the project already uses or can reasonably adopt it;
- WebGL2 as the compatibility renderer;
- WebGPU as an optional/high-end renderer, not the only path unless project requirements justify it;
- `requestAnimationFrame`/Emscripten main-loop APIs rather than a blocking native loop;
- preloaded files for immutable assets and OPFS/IndexedDB for persistent saves;
- WebAssembly SIMD only behind capability checks;
- pthreads only with correct COOP/COEP headers and a single-thread fallback where practical.

## Validation loop

For every port milestone:

1. build native reference;
2. build Wasm;
3. start a local HTTP server with any required COOP/COEP headers;
4. launch Chromium/Firefox;
5. capture console errors;
6. run deterministic input for a fixed number of frames;
7. compare stable observables (state hashes, memory checkpoints, audio hashes where practical, screenshots with tolerance);
8. record the exact command and result.

Prefer verifier-guided agent loops over speculative large rewrites.

## Commands in this repo

```bash
python portctl.py list
python portctl.py doctor
python portctl.py fetch <group>
python portctl.py new <name> --platform <platform>
```

Read `docs/PORTING_MATRIX.md` and `docs/WEB_TARGET.md` before selecting a route.
