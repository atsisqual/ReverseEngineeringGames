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

- `upstream/retroReversing/` — pinned `RetroReversing/retroReversing` submodule used as the first-stop knowledge base for console architecture, SDKs, file formats, existing source/reversing projects and tools.
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

Executable third-party tool projects are normally cloned by `portctl.py fetch ...` under ignored `.tools/`. The RetroReversing knowledge base is different: it is pinned as a Git submodule so agents can search it locally without copying its history into this repository.

## Quick start

```bash
git submodule update --init --recursive
python portctl.py list
python portctl.py route n64
python portctl.py doctor
python portctl.py fetch web
python portctl.py fetch n64
python portctl.py new my-game --platform n64
```

Before doing new platform/tool research, search `upstream/retroReversing/` first.

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
