# Ogre Battle 64 browser reference target

This is the first **real commercial-game reference target** in ReverseEngineeringGames.
The game-specific code lives upstream at `lfarroco/ogre-battle-64-recomp`; this
repository only stores orchestration, audit rules and pinned public revisions.
No ROM, generated recompiled game code, save data or extracted commercial assets
are included here.

## Why this target

The upstream project has already demonstrated the difficult N64Recomp browser
path rather than merely compiling a toy program:

- N64Recomp-generated game code runs under Emscripten;
- N64ModernRuntime has Emscripten compatibility patches for memory, threads,
  live-recompiler/JIT behavior and window handles;
- the browser boot reaches real RSP display-list submission;
- keyboard/gamepad input, AudioWorklet plumbing and IDBFS persistence exist;
- a WebGL2 renderer prototype processes real display lists;
- current rendering is **not complete**: the title sprite layer renders, while
  S2DEX2 and parts of the game's 3D/menu rendering remain incorrect.

That makes it a useful reference implementation and a much stronger starting
point for extracting reusable N64-to-web techniques than an emulator-only demo.

## Pinned revisions

See `target.json`. The target pins both the game repository and the runtime/
N64Recomp revisions used by its public patch set. Do not silently move these
pins: audit and build behavior must remain reproducible.

## Reproduce locally

Prerequisites include Git, CMake, Make, an activated Emscripten SDK and, for
regenerating the game code, MIPS GNU binutils. The script never downloads a ROM.

```bash
python targets/ogre-battle-64/prepare.py doctor --regen
python targets/ogre-battle-64/prepare.py clone
python targets/ogre-battle-64/prepare.py tools
python targets/ogre-battle-64/prepare.py stage-rom /path/to/your/ogre-battle-64-rev-a.z64
python targets/ogre-battle-64/prepare.py regenerate
python targets/ogre-battle-64/prepare.py build-web
python targets/ogre-battle-64/prepare.py serve
```

Or run the complete pipeline:

```bash
python targets/ogre-battle-64/prepare.py all /path/to/your/ogre-battle-64-rev-a.z64
```

Then open the URL printed by the upstream server (normally
`http://127.0.0.1:8931/app/web/index.html`). The server supplies the COOP/COEP
headers required by Wasm pthreads/`SharedArrayBuffer`.

The local input check verifies a 40 MiB big-endian `.z64` container and N64
header magic. The upstream runtime performs the authoritative XXH3-64 check
against `be6adaa5c3f8f7a9` before using the game.

## Audit any N64 recomp project

The reusable part is `tools/n64_web_audit.py`:

```bash
python tools/n64_web_audit.py /path/to/an/n64-recomp-project
python tools/n64_web_audit.py /path/to/an/n64-recomp-project --strict
python tools/n64_web_audit.py /path/to/an/n64-recomp-project --json
```

It looks for concrete evidence of Emscripten integration, runtime Wasm work,
threads, memory strategy, browser renderer, input/audio, persistence,
cross-origin isolation and browser smoke testing. It is a readiness audit, not
a proof of rendering correctness.
