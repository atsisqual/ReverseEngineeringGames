# Porting matrix: original game -> browser

The browser side is comparatively standardized: WebAssembly plus browser graphics/audio/input/storage APIs. The hard part is obtaining a portable CPU/game-code representation and a runtime that does not assume native OS features.

Legend:

- **Good**: established route; game-specific work still required.
- **Possible**: tools exist, but runtime/browser adaptation is substantial.
- **Fallback**: compile an emulator/core to WebAssembly rather than producing a native-style port.
- **Research**: no general route should be assumed.

| Input family | Reverse-engineering / recomp tools | Browser route | Confidence |
|---|---|---|---|
| Existing C/C++ source or matching decomp | project build + `objdiff` where applicable | Emscripten -> Wasm | Good |
| N64 | N64Recomp, `objdiff`, platform decomp tooling | generated C or decomp source -> browser runtime -> Emscripten | Possible |
| GameCube / Wii | DolRecomp, decomp-toolkit, objdiff | generated C/decomp source -> replace/adapt runtime -> Emscripten | Possible |
| Wii U | DolRecomp has early Espresso/RPX support | same conceptual route, significantly more runtime work | Research |
| PS1 | matching-decomp ecosystems + objdiff | portable decomp source -> Emscripten | Possible |
| PS2 | matching-decomp ecosystems + objdiff | portable decomp source -> Emscripten | Possible/Research |
| PSP | matching decomp + objdiff | portable source -> Emscripten | Possible |
| Dreamcast/Saturn | objdiff supports SuperH comparison; project-specific tooling | source route if decomp exists; otherwise emulator-core fallback | Research |
| Old Win32 x86 C++ | Ghidra + `reccmp` for supported older MSVC projects | matching decomp -> remove Win32/DirectX assumptions -> Emscripten | Possible |
| Modern closed Windows game | Ghidra/analysis only; no universal recompiler | obtain source, reimplement legally, or use streaming/emulation | Research |
| DOS | mature DOS emulators | emulator/core -> Wasm | Fallback |
| Java/J2ME | source/decompiler + JVM-specific web runtime | project specific | Research |
| Flash | SWF runtime projects | run via a browser-compatible Flash reimplementation rather than "porting" | Fallback |
| Unity binary only | no generic binary-to-WebGL conversion | requires project/source for normal Unity WebGL export | Research |
| Unreal binary only | no generic binary-to-browser conversion | requires source/project or project-specific reimplementation | Research |

## Core tools

### Emscripten

Primary C/C++ -> WebAssembly toolchain. It uses Clang/LLVM and emits JavaScript/browser glue. For game ports it is especially useful because it also provides browser-facing support for SDL-style input/audio, OpenGL-to-WebGL translation, filesystems, pthreads and POSIX-like APIs.

### Binaryen

WebAssembly optimization/tooling layer. `wasm-opt` is useful for size/performance passes, validation and debugging generated Wasm.

### WABT

Low-level WebAssembly inspection suite (`wasm2wat`, `wasm-objdump`, `wasm-validate`, etc.). Use it when the Wasm itself is suspect.

### objdiff

Cross-architecture object diffing and matching-decomp verification. It supports ARM, ARM64, MIPS, PowerPC, SuperH, x86 and x86_64 families, making it one of the most reusable RE tools in this repo.

## Static recompilation paths

### N64Recomp

N64Recomp translates N64 binaries to C and is built for static recompilation. It is a strong CPU-side front-end, but generated C is not a complete web game: the runtime, renderer, audio and platform integration still need browser-compatible implementations.

Recommended experiment:

1. get a known native recomp project running;
2. compile generated CPU C with Emscripten in isolation;
3. identify native-only runtime surfaces;
4. create/port a WebGL2/WebGPU + WebAudio + Gamepad host;
5. add deterministic state/frame comparisons against the native build.

### DolRecomp

DolRecomp recompiles GameCube/Wii PowerPC code and offers C/LLVM backends. Upstream explicitly scopes it to the CPU side; graphics, audio, input and platform integration belong to the host runtime. This separation is useful for a browser port because the browser work can concentrate on the host/runtime boundary.

`ModernGekko` is a useful native runtime/reference implementation, but do not assume it can simply be passed to Emscripten unchanged: Dolphin-derived/native dependencies must be audited one by one.

For source-level GameCube/Wii matching decomp, use `decomp-toolkit` + `objdiff`.

## Matching decompilation path

When a static recompiler is absent or unsuitable:

```text
binary -> analysis -> matching source -> portable source -> Emscripten
                 \-> verifier <---------/
```

A coding agent works best when the verifier supplies an objective score. `objdiff`, `reccmp` and project-specific diff scripts turn decompilation into an edit/build/compare loop.

`reccmp` is particularly useful for older 32-bit x86 C++ built with older MSVC versions. Do not generalize it to every x86 game.

## Emulator-core fallback

Sometimes "native-style browser port" is the wrong engineering objective. If:

- the platform already has a mature portable emulator core;
- the title uses self-modifying code/JIT-heavy behavior;
- the runtime/HLE surface is much larger than the game logic;
- there is no matching-decomp/static-recomp ecosystem;

then compiling the emulator/core to Wasm may reach a playable browser result much sooner. Keep this route explicitly labeled as emulation, not recompilation.

## AI-assisted workflow

AI coding agents help most when the repository exposes small deterministic tools:

```text
inspect symbol
-> edit one unit
-> build
-> run objdiff/reccmp/custom verifier
-> run headless/browser smoke test
-> compare trace/state
-> commit measurable improvement
```

Do not let an agent replace verifier output with visual guesses.
