# ReverseEngineeringGames

An AI-friendly toolbox for taking **legally obtained game code/binaries** through reverse engineering, decompilation, static recompilation or a browser-capable emulator path and targeting a modern **web browser**.

> There is no universal `ROM/EXE -> browser` converter. The browser target is common (WebAssembly + browser APIs); the best front-end depends on the original platform and on what source/decomp/recomp/runtime work already exists.

## Start with the route resolver

Before cloning tools, ask the repo which path is currently preferred:

```bash
python portctl.py route n64
python portctl.py route gamecube
python portctl.py route ps2
python portctl.py route psx
python portctl.py route psp
python portctl.py route mystery-console --json
```

Examples of the current strategy:

| Platform | Preferred browser route today |
|---|---|
| Portable source / matching decomp | Emscripten directly |
| N64 | N64Recomp / source port first; real Ogre Battle 64 browser reference; N64Wasm fallback |
| GameCube / Wii | DolRecomp + GXRuntime/ModernGekko; CPU/AOT + WebGPU core exist, browser host/surface remains work |
| PS2 | Official Play! Emscripten/browser build as execution fallback |
| PSP | Community PPSSPP-Web reference |
| PS1 | Official RetroArch Emscripten frontend + browser-capable libretro core |
| NES/SNES/GB/GBA/Genesis | RetroArch Web Player + compatible core |
| Older 32-bit Windows | matching decomp/static recomp; `recomp-kit` where compatible |
| Unknown platform | research source/decomp/recomp first, then mature WebAssembly emulator fallback |

The machine-readable registry lives in `routes.json`.

## Architecture

```text
                 original game you own
                         |
        +----------------+----------------+
        |                |                |
   source/decomp     static recomp     emulation fallback
        |                |                |
   C / C++ / Rust    generated C/LLVM   mature emulator core
        |                |                |
        +---------- Emscripten / LLVM ----+
                         |
                  WebAssembly (.wasm)
                         |
        +----------------+----------------+
        |                |                |
     WebGL2/WebGPU     WebAudio      Gamepad/Keyboard
        |                |                |
        +----------- browser shell -------+
```

## What is in this repo

- `portctl.py` — route resolver, prerequisite doctor, upstream tool fetcher and per-game scaffold.
- `routes.json` — platform -> preferred route/status/tools/fallbacks.
- `toolchains.json` — curated upstream tool registry grouped by platform/purpose.
- `AGENTS.md` — rules for Codex/Claude-style coding agents.
- `labs/n64-web/` — executable native/Emscripten host probe with N64 controller mapping and browser capability checks.
- `targets/ogre-battle-64/` — pinned **real N64Recomp browser reference target** using only a locally supplied ROM.
- `tools/n64_web_audit.py` — N64 browser-readiness audit.
- `targets/gcwii-web-gap/` + `tools/gcwii_web_audit.py` — pinned GameCube/Wii gap map that distinguishes GXRuntime's existing WebGPU renderer core from the missing browser platform/surface host.
- `targets/web-fallbacks/` + `tools/web_reference_audit.py` — pinned PS2/PSP/RetroArch browser reference checks.
- `docs/N64_WEB.md`, `docs/GCWII_WEB.md`, `docs/EMULATION_FALLBACKS.md` — current platform findings.
- `docs/PORTING_MATRIX.md`, `docs/WEB_TARGET.md`, `docs/LEGAL.md` — general porting/browser/legal guidance.
- `web-shell/` — minimal browser capability probe.

Third-party projects are not vendored. `portctl.py fetch ...` clones them under `.tools/`, which is ignored by Git.

## Quick start

```bash
python portctl.py list
python portctl.py route n64
python portctl.py doctor
python portctl.py fetch web
python portctl.py fetch n64
python portctl.py new my-game --platform n64
```

For the browser execution references:

```bash
python portctl.py fetch web-emulation   # Play!, RetroArch, Beetle PSX, PPSSPP-Web
python portctl.py fetch browser-reference
```

For N64-specific work:

```bash
python portctl.py fetch n64-web
python tools/n64_web_audit.py /path/to/an/n64-recomp-project --strict
```

For GameCube/Wii research:

```bash
python portctl.py fetch gcwii
python tools/gcwii_web_audit.py /path/to/GXRuntime --strict-foundation
```

## Verified reference paths

### N64 static recompilation

The repo tracks a pinned Ogre Battle 64 browser reference demonstrating that N64Recomp-generated code can run under Emscripten with browser input/audio/persistence and a WebGL2 renderer prototype. Rendering coverage is still title/microcode-specific, so a linked `.wasm` is not considered a completed port.

### GameCube / Wii static recompilation

DolRecomp/GXRuntime/ModernGekko provide a strong native AOT/runtime foundation. GXRuntime already contains a Dawn/WebGPU renderer substrate. The current missing layer is the actual Emscripten/browser platform + canvas/surface + browser host integration; CI intentionally watches that gap.

### PS2 browser fallback

Play! officially supports Emscripten/browser builds and an experimental browser frontend. It uses a built-in HLE BIOS, so this route does not require shipping a PS2 BIOS image.

### PSP browser fallback

The tracked PPSSPP-Web route is a community project, not an official PPSSPP release. The repo labels it accordingly.

### PS1/classic browser fallback

RetroArch provides an official Emscripten frontend with documented WebGL, threaded builds, AudioWorklet, WasmFS/OPFS and COOP/COEP support. The individual libretro core must also support the web target.

## Browser reality

CPU translation is only one part of a browser port. A complete result may still need:

- graphics -> WebGL2/WebGPU;
- audio -> WebAudio / AudioWorklet;
- input -> Gamepad/Keyboard/Pointer;
- filesystem/saves -> IDBFS/OPFS/WasmFS;
- networking -> WebSocket/WebTransport-compatible paths;
- threads -> Wasm pthreads plus cross-origin isolation;
- native JIT/executable-memory/dynamic-library behavior -> browser-safe alternatives.

Use deterministic state/frame comparisons and real browser smoke tests. Do not call a port complete merely because C/C++ compiles to `.wasm`.

## Project policy

This repository intentionally contains no ROMs, ISOs, BIOS/firmware images, keys, extracted commercial assets or proprietary SDK/compiler binaries. Bring your own legally obtained inputs and keep them outside Git; generated workspaces and original-content directories are ignored.

## Status

This is now a **route-driven reverse-engineering/browser-port toolbox** rather than a claim that every platform has the same path. Some routes are real static-recomp browser references, some are explicit engineering gaps, and some are verified emulator fallbacks. CI continuously checks those distinctions against pinned public upstream projects so agents do not work from stale assumptions.
