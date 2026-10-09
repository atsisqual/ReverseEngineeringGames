# N64 browser strategy

Status date: 2026-10-09.

## What is verified upstream

- N64Recomp statically translates N64/MIPS functions to portable C and explicitly expects a runtime to provide macros/platform behavior.
- N64ModernRuntime provides `ultramodern` + `librecomp`; projects provide callbacks for input/audio and must register a renderer.
- N64ModernRuntime's current public renderer header has platform window-handle branches for Windows, Linux/Android and Apple, but no Emscripten branch.
- N64Wasm is a WebAssembly N64 emulator and is the immediate fallback when a true static port is not yet practical.
- Emscripten SDK `latest` currently resolves to 6.0.12; this repo pins 6.0.12 in CI so browser-probe breakage is reproducible.
- `recomp-kit` demonstrates a modern recomp-to-browser architecture (WebGPU + pthreads + WasmFS) for 32-bit x86 Windows games. It is architectural evidence, not an N64 runtime.

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
  |                                                     +-> browser input/audio adapters
  |                                                     +-> WEB RENDERER (open blocker)
  |
  +-- need browser execution now? -------- yes --> N64Wasm emulator fallback
```

## Browser-runtime work packages

1. **Input**: implemented in `labs/n64-web`; map standard Gamepad API to N64 buttons/stick and optional rumble.
2. **Audio**: implement N64ModernRuntime's `audio_callbacks_t` on top of WebAudio/AudioWorklet (or SDL audio as an interim adapter).
3. **Renderer**: the main blocker. Provide a `RendererContext` implementation backed by WebGPU/WebGL and an RSP/RDP path compatible with the target game.
4. **Window handle**: upstream runtime needs an Emscripten-safe `WindowHandle` representation before it can be compiled unchanged for Wasm.
5. **Saving**: bridge EEPROM/SRAM/Flashram persistence to browser storage (OPFS/IndexedDB/WasmFS strategy depends on runtime choice).
6. **Threads**: compile with Wasm pthreads only after serving COOP/COEP headers and auditing blocking waits.
7. **Validation**: compare deterministic game state/frame checkpoints against a native reference; rendering screenshots alone are insufficient.

## Agent rule

An AI agent must not mark the static-recomp browser route as complete merely because generated C compiles to `.wasm`. Completion requires at least controller input, audio, saving and actual RSP/RDP-rendered gameplay in a browser.
