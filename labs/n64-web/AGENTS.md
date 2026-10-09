# N64 web lab agent instructions

Scope: `labs/n64-web/` and documentation that explicitly references this lab.

Goal: turn N64 ports into browser builds without confusing CPU recompilation with a complete port.

Work in this order:

1. Keep the native smoke build green.
2. Keep the Emscripten smoke build green.
3. Integrate one N64ModernRuntime callback family at a time: input, audio, saving, then renderer.
4. For every runtime integration, add a deterministic test or observable browser probe.
5. Do not vendor ROMs, extracted commercial assets, firmware, keys or proprietary SDK/compiler files.
6. Do not copy code from a reference project until its license is identified and compatible with the intended use.
7. Do not claim a game is ported when only generated C or Wasm exists. A complete milestone requires actual gameplay with rendering, input, audio and saving in a browser.

Renderer work must document which RSP/RDP implementation is being used and why it can legally and technically target WebGPU/WebGL.

Prefer small adapter layers over forks of N64Recomp/N64ModernRuntime. If an upstream patch becomes necessary, isolate it and explain why the public callback surface is insufficient.
