# GameCube / Wii → browser strategy

Status date: 2026-10-09.

## Current reality

The CPU/static-recomp side is strong; the browser host is the missing layer.

- **DolRecomp** recompiles GameCube/Wii PowerPC DOL/REL code to C and also has an LLVM backend.
- **ModernGekko** is the ExpansionPak runtime for native recomp projects.
- **GXRuntime** is a game-agnostic runtime with PPC semantics, devices and a GX renderer. Its CPU semantics are validated against Dolphin's interpreter and its public README reports full-game rendering through its current desktop/Aurora host.
- **RecompCore** is the accuracy/oracle route: statically recompiled code runs inside a Dolphin-derived runtime with interpreter fallback/lockstep.
- As of this snapshot, searches of the current public ModernGekko/GXRuntime trees do **not** expose a completed Emscripten + WebGL/WebGPU browser backend comparable to the N64 Ogre Battle reference.

So the recommended engineering path is not "rewrite the CPU". It is:

```text
GameCube/Wii DOL + RELs
        |
     DolRecomp
        |
 generated C / LLVM AOT
        |
 GXRuntime / ModernGekko core
        |
  +-----+------------------------+
  |                              |
Emscripten host              correctness oracle
  |                           RecompCore/Dolphin
WebAssembly
  |
WebGPU/WebGL + WebAudio + Gamepad + browser storage
```

## Browser work packages

1. Prove the headless/runtime core compiles with Emscripten without the Aurora/native window backend.
2. Define a Wasm-safe guest-memory model and remove native VM/executable-memory assumptions.
3. Keep the AOT path JIT-free.
4. Port GX command processing/presentation to WebGPU or WebGL2; preserve a measurable GX-register/opcode coverage gate.
5. Add browser input, audio and persistent memory-card/save storage.
6. If pthreads are needed, use a worker architecture and COOP/COEP isolation.
7. Validate PPC state and GX output against RecompCore/Dolphin before optimizing.

## Mechanical gap check

```bash
python tools/gcwii_web_audit.py /path/to/GXRuntime --strict-foundation
```

The pinned gap target intentionally expects these rules to be missing today:

```text
emscripten-build
browser-renderer
cross-origin-isolation
```

CI fails if those expectations change. That is deliberate: when upstream gains a browser backend, this repository should stop calling it a gap and promote it to a real browser reference target.
