# N64ModernRuntime → browser compatibility checklist

Use this when adapting a new N64Recomp title. It is distilled from public N64
browser-port work and intentionally avoids copying game-specific code.

## Runtime

- Provide an explicit `__EMSCRIPTEN__` window-handle/platform branch.
- Replace native virtual-address reservation/guard-page allocation with a
  WebAssembly-safe heap allocation strategy.
- Guard native-only backtrace, OS scheduling/priority and executable-memory APIs.
- Disable or provide a no-op/browser-safe implementation of LiveRecomp/JIT.
- Confirm pointer-width assumptions: Wasm32 exposes 32-bit native pointers even
  though guest N64 addresses/registers may be represented with wider integers.

## Threads

- Build with `-pthread` and a pool sized for runtime workers plus the game's N64
  thread population.
- Never block the browser main thread in the runtime's native update loop.
- Serve with `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: require-corp`.
- Treat timing-sensitive queues/semaphores as validation targets; browser worker
  scheduling can expose bugs hidden on desktop.

## Memory and storage

- Set `INITIAL_MEMORY`/`MAXIMUM_MEMORY` deliberately. Large N64Recomp runtimes can
  need hundreds of MiB before game assets and renderer allocations.
- If JS/AudioWorklet holds pointers into Wasm memory, avoid memory growth or add
  a robust rebinding mechanism when the buffer moves.
- Persist saves/config via IDBFS, OPFS or WasmFS; keep user-owned ROMs local and
  validate them before boot.

## Platform callbacks

- Input: browser Gamepad/keyboard → runtime controller callbacks.
- Audio: runtime PCM queue → AudioWorklet/WebAudio, with explicit sample-rate
  conversion and underrun metrics.
- Rumble: browser Gamepad haptics where available, best-effort only.
- Error/quit/UI callbacks must not assume desktop windows or process APIs.

## Renderer

- Start with a null renderer and prove CPU/runtime/display-list milestones first.
- Inventory microcodes and GBI opcodes from real workloads before claiming
  renderer coverage.
- Implement F3DEX/F3DEX2/S2DEX variants based on what the target actually uses.
- Validate TMEM/load-block semantics, render modes, framebuffer/VI behavior,
  scissoring, texture formats, depth/blending and sprite paths against native
  reference captures.
- Keep workload statistics available in-browser so an agent can see unsupported
  opcodes rather than guessing from a screenshot.

Run `python tools/n64_web_audit.py <tree> --strict` for a mechanical first pass.
