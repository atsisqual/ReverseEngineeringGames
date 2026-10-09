# Web target engineering notes

A successful native build is only the midpoint. Browsers deliberately do not expose the same process, memory, graphics, filesystem and networking model as Windows/Linux/macOS/consoles.

## Baseline target

Default compatibility target:

- WebAssembly;
- Emscripten;
- WebGL2 renderer;
- WebAudio;
- Gamepad + keyboard/mouse;
- Emscripten virtual filesystem;
- HTTP(S) asset loading.

Optional/high-end:

- WebGPU;
- Wasm SIMD;
- Wasm threads;
- OPFS for persistent high-volume storage.

## Main loop

Native games often block forever:

```cpp
while (running) {
    poll();
    update();
    render();
}
```

A browser needs to return control to the event loop. With Emscripten use its main-loop APIs or an equivalent requestAnimationFrame-driven host.

Do not emulate a blocking loop with long synchronous JavaScript calls.

## Graphics

### Easiest path

Existing OpenGL ES 2/3-like code -> Emscripten -> WebGL.

### Harder paths

- fixed-function / desktop-only OpenGL: create a compatibility translation layer or modernize it;
- Direct3D: renderer abstraction or API translation/reimplementation is usually required;
- console GX/RDP/custom GPU command streams: use an existing HLE/runtime renderer as reference, but build a WebGL2/WebGPU backend rather than assuming CPU recompilation solves graphics.

Treat WebGPU as an additional backend unless the project explicitly accepts narrower browser/device support.

## Audio

SDL audio is often the shortest route because Emscripten maps it to browser audio facilities. Custom low-latency mixers need special attention to buffering and the browser's autoplay/user-gesture rules.

## Input

Map the game's logical controller model onto:

- Gamepad API;
- keyboard/mouse;
- pointer lock for relative mouse controls;
- touch controls when relevant.

Do not expose browser key codes directly throughout game logic; keep a stable logical input layer.

## Files and saves

Native absolute paths and arbitrary filesystem access do not exist.

Use:

- preloaded/package files for immutable game-owned data;
- MEMFS for temporary files;
- IDBFS or OPFS-backed storage for saves/configuration;
- user file picker for user-supplied original game data when the architecture supports runtime loading.

Never embed commercial game images into the published web bundle.

## Threads

WebAssembly pthreads require browser cross-origin isolation. Your server generally needs:

```text
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

That deployment requirement is important enough to test early.

Keep a single-thread mode when performance permits, because it makes local hosting and embedding much easier.

## Networking

Browser code cannot open arbitrary native TCP/UDP sockets.

Possible replacements:

- WebSocket;
- WebTransport where appropriate and available;
- HTTP/fetch;
- WebRTC for peer-to-peer use cases.

A game protocol that assumes raw UDP requires an adapter/proxy or a protocol rewrite.

## Dynamic code and modules

Browsers do not provide general-purpose executable-memory/JIT behavior to Wasm code in the same way a native process does.

Audit:

- `mmap(PROT_EXEC)` / `VirtualAlloc(...EXECUTE...)`;
- runtime code generation;
- native `.dll/.so/.dylib` loading;
- inline assembly tied to host CPU;
- signals/SEH assumptions.

Static recompilation is often attractive precisely because it can eliminate guest JIT needs.

## Endianness and alignment

Console code may assume big-endian memory layout or hardware-specific unaligned behavior. Do not "fix" these opportunistically; make guest-memory semantics explicit and test them.

Wasm memory itself is byte-addressable and the compiler target is little-endian, so guest-endian access helpers are often required.

## 32-bit pointers / memory

Many older games assume a 32-bit address space. Wasm32 can be convenient, but code that casts pointers to integer guest addresses still needs a disciplined memory model.

Avoid relying on native address identity.

## Browser smoke-test checklist

Before gameplay:

- [ ] `.wasm` loads over HTTP, not `file://`;
- [ ] no missing imports;
- [ ] canvas/context initializes;
- [ ] audio starts after a user gesture;
- [ ] gamepad enumerates after interaction;
- [ ] saves survive reload;
- [ ] fullscreen/pointer-lock paths work;
- [ ] no cross-origin isolation error if threads are enabled;
- [ ] deterministic fixed-frame run completes;
- [ ] console has no uncaught errors.
