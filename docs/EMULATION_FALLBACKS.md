# Browser emulation fallbacks

Static recompilation or a source port is preferable when a mature route exists, but it is not necessary to block browser execution while reverse-engineering work catches up. This document records verified browser-capable emulator/front-end routes.

## PS2 — Play! (official)

Play! explicitly supports a web-browser platform. Its upstream build instructions use Emscripten/`emcmake` and produce `Play.js` + `Play.wasm` for the `js/play_browser` frontend. The upstream project calls the browser build experimental and documents browser-specific memory/JIT and floating-point caveats. It uses an HLE BIOS, so it does not require a Sony BIOS file.

Use this as the default PS2 browser fallback before attempting a game-specific PS2 decomp/recomp.

## PSP — PPSSPP WebAssembly community fork

`root-hunter/ppsspp-web` is a community project, not an official PPSSPP release. It pins a PPSSPP WebAssembly source/build submodule, provides a browser UI and an HTTPS server with COOP/COEP headers, and has reproducible `make wasm-dev` / `make serve` flows.

Use it as a research/reference path, and keep the community status explicit.

## PS1 and classic consoles — RetroArch Web Player

RetroArch has an official Emscripten frontend. Its current documentation covers single-threaded and pthread builds, WebGL, AudioWorklet, WasmFS/OPFS support, and the COOP/COEP headers required for threaded cores. A specific libretro core still needs to support Emscripten.

For PS1, Beetle PSX contains Emscripten-specific code paths; other libretro PS1 cores can also be investigated depending on performance/accuracy requirements. For NES/SNES/GB/GBA/Genesis and many other classic systems, the RetroArch Emscripten frontend is the common browser host and the core is the replaceable component.

## Rule

These are **execution fallbacks**, not substitutes for a decomp/recomp when the goal is a native-style port. A route may be good enough to play in a browser while still being the wrong architecture for widescreen patches, engine-level mods, VR conversion or deep source-level changes.

Use `python portctl.py route <platform>` to see the current preferred route and fallback tools.
