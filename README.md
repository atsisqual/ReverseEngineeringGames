# ReverseEngineeringGames

A practical, AI-friendly toolbox for taking **legally obtained game code/binaries** through reverse engineering, decompilation or static recompilation and, where the platform/runtime allows it, shipping the result to a modern **web browser**.

> There is no universal "ROM/EXE -> browser" converter. The browser target is common (WebAssembly + Web APIs), but the front-end depends on the original platform and on how much source/decomp/recomp infrastructure already exists.

## Architecture

```text
                 original game you own
                         |
        +----------------+----------------+
        |                |                |
   source/decomp     static recomp     emulation fallback
        |                |                |
   C / C++ / Rust    generated C/LLVM   existing emulator core
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

## What this repo gives you

- `portctl.py`: one CLI to inspect the host, fetch selected upstream toolchains and scaffold a web-port workspace.
- `toolchains.json`: curated upstream tool registry grouped by purpose/platform.
- `AGENTS.md`: operating rules for Codex/Claude-style coding agents.
- `docs/PORTING_MATRIX.md`: which route to try for each family of platforms.
- `docs/WEB_TARGET.md`: browser/Wasm constraints that commonly break native game ports.
- `docs/LEGAL.md`: clean-room / copyrighted-input guardrails.
- `web-shell/`: minimal browser capability probe useful before starting a port.

Third-party tools are **not vendored** into this repository. `portctl.py fetch ...` clones them under `.tools/`, which is gitignored. This keeps their licenses/history intact and makes upgrades explicit.

## Quick start

Requirements: Python 3.10+, Git, CMake, Ninja, Clang/LLVM and Node.js. For actual browser builds, install Emscripten (or let `portctl.py` fetch `emsdk`).

```bash
python portctl.py list
python portctl.py doctor
python portctl.py fetch web
python portctl.py fetch n64
python portctl.py new my-game --platform n64
```

Then initialize Emscripten in your shell using the upstream SDK instructions and validate it:

```bash
python portctl.py doctor --strict
```

Serve the browser probe locally:

```bash
python -m http.server 8000 -d web-shell
```

Open `http://localhost:8000`.

## Recommended route by input

| Starting point | First route |
|---|---|
| Portable C/C++ source or matching decomp | Emscripten directly |
| N64 binary + symbols/decomp metadata | N64Recomp -> C/runtime -> adapt runtime to Emscripten |
| GameCube/Wii DOL/REL | DolRecomp or source decomp -> browser-compatible runtime -> Emscripten |
| PS1/PS2/PSP matching decomp | Source/decomp -> Emscripten; use `objdiff` during matching |
| Old 32-bit Windows C++ | Matching decomp (`reccmp` where applicable) -> modern portable source -> Emscripten |
| DOS / machine with mature emulator core | Compile emulator core to Wasm when a native recomp/decomp route is impractical |
| Unity/Unreal/closed modern binaries | No generic static port path; obtain source or use a legitimate streaming/emulation approach |

See `docs/PORTING_MATRIX.md` for the detailed matrix and limitations.

## Tool groups

```bash
python portctl.py fetch web       # emsdk, Binaryen, WABT
python portctl.py fetch analysis  # Ghidra source, objdiff, decomp-toolkit
python portctl.py fetch agents    # verifier-guided agent harness
python portctl.py fetch n64       # N64Recomp + N64ModernRuntime
python portctl.py fetch gcwii     # DolRecomp + ModernGekko + decomp-toolkit
python portctl.py fetch pc        # reccmp
python portctl.py fetch all
```

Use `--dry-run` before cloning, `--update` to fast-forward existing clones, and `--depth 1` for shallow clones.

## Important browser reality

The CPU translation is only part of a port. A working browser version must also replace or adapt:

- graphics -> WebGL2 or WebGPU;
- audio -> WebAudio (often via SDL);
- input -> Gamepad/Keyboard/Pointer APIs;
- filesystem -> Emscripten VFS / OPFS / IndexedDB;
- sockets -> WebSocket/WebTransport-compatible networking;
- threads -> WebAssembly threads, which require cross-origin isolation;
- native dynamic libraries / JIT / executable memory -> browser-safe alternatives.

A static recompiler that emits C is useful because the generated C can *potentially* be compiled by Emscripten, but its native runtime may still depend on APIs that do not exist in browsers.

## Project policy

This repo intentionally contains no ROMs, ISOs, keys, firmware, extracted commercial assets or proprietary SDK/compiler binaries. Bring your own legally obtained inputs and keep them outside Git; generated workspaces ignore `original/`, `roms/`, `iso/`, `assets-original/` and similar paths.

## Status

This is a **toolbox and workflow scaffold**, not a claim that every listed platform can already be recompiled to a browser. The goal is to make the route, blockers and verification loop explicit so an AI coding agent can work productively instead of guessing.
