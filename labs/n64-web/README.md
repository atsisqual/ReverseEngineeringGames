# N64 -> browser lab

This is the first executable browser-target experiment in this repository. It deliberately separates three routes instead of pretending that every N64 title has the same path.

## Route A: source / matching decomp (recommended when available)

Compile the portable game code with Emscripten and replace platform pieces with Web APIs. This is the cleanest route because the browser sees normal C/C++ rather than a console runtime that was designed around desktop graphics APIs.

## Route B: N64Recomp (experimental browser route)

`N64Recomp` emits C that can be compiled by normal C compilers. `N64ModernRuntime` bridges that generated code to libultra-style services, but its current renderer abstraction still expects a platform-specific `WindowHandle` and recommends RT64. As of 2026-10-09 there is no public Emscripten/WebGPU backend in N64ModernRuntime/RT64 that this repository can simply switch on.

The code in this directory starts the missing browser-host layer with pieces that are independent of the renderer:

- browser-standard Gamepad -> N64 button/stick state;
- right stick -> C-buttons;
- best-effort Gamepad vibration;
- WebGPU capability detection;
- cross-origin-isolation detection;
- a tiny Emscripten smoke target.

The shape intentionally matches what N64ModernRuntime asks the project to provide: controller polling/rumble and, later, audio plus a renderer callback implementation. Do **not** patch upstream blindly. Keep browser-specific work here until the contract is proven by a real title.

### Remaining blocker for a real recomp game

A renderer implementation must consume the game's RSP/RDP work and present it through WebGPU/WebGL. CPU recompilation alone is not enough. Candidates to research are:

1. add a WebGPU backend to an RT64-compatible path;
2. adapt a browser-capable RDP implementation;
3. for a specific decomp, bypass the recomp runtime and port its renderer directly.

## Route C: emulator-core fallback (works today)

When the goal is simply to run an N64 title in a browser rather than produce a native-style static port, `N64Wasm` is a proven WebAssembly fallback. Fetch it with:

```bash
python portctl.py fetch n64-web
```

Keep this route conceptually separate from a static recomp port: it is an emulator compiled to Wasm.

## Build this probe

Native syntax/smoke build (does not use browser APIs):

```bash
cmake -S labs/n64-web -B build/n64-native -G Ninja
cmake --build build/n64-native
./build/n64-native/reg_n64_web_smoke
```

Web build with Emscripten 6.0.12 or newer:

```bash
source .tools/emsdk/emsdk_env.sh
emcmake cmake -S labs/n64-web -B build/n64-web -G Ninja
cmake --build build/n64-web
python labs/n64-web/serve.py --dir build/n64-web
```

Then open `http://127.0.0.1:8000/reg_n64_web_smoke.html` and press a gamepad button. The overlay reports WebGPU, cross-origin isolation and the mapped N64 controller state.

## Why the isolation headers?

Serious browser ports often need Wasm threads. `SharedArrayBuffer`/pthreads require a cross-origin-isolated page, so the local server always sends COOP/COEP headers. This also mirrors the setup used by newer WebGPU recomp projects.

## Reference project found during research

`veritr1x/recomp-kit` is **not an N64 tool**; it recompiles 32-bit x86 Windows games. It is nevertheless a useful current reference because it already ships a browser target built around Emscripten, WebGPU, pthreads and WasmFS. It is registered as a reference tool, not copied into this repository. Review its license before borrowing code.
