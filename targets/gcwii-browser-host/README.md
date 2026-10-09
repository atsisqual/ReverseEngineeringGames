# GXRuntime browser-host patch target

This target is the first step that applies the browser work to the **real pinned
GXRuntime/Aurora tree**, rather than another standalone WebGPU probe.

It does not fork or vendor GXRuntime. `apply.py` only accepts the pinned public
commit and performs exact-string transformations. If the upstream source changes,
the patcher fails rather than guessing.

## Changes applied

- replace native Dawn dependency resolution with Emscripten's official
  `emdawnwebgpu` port;
- expose `BACKEND_WEBGPU` in Aurora's browser build;
- compile `BackendBinding.cpp` without the native Tracy/Dawn platform layer;
- create the WebGPU surface from HTML canvas `#canvas`;
- omit the native `TimedWaitAny` instance requirement on Emscripten;
- retain Aurora's synchronous `webgpu::initialize()` contract with Asyncify and
  `emscripten_sleep(0)` around adapter/device callbacks;
- leave native Dawn paths unchanged.

## Reproduce

```bash
git clone https://github.com/aharonahdoot/GXRuntime.git /tmp/gxruntime
git -C /tmp/gxruntime checkout 8a47b0e8ea7dfc39014a4cff4f7895d88494a611
python targets/gcwii-browser-host/apply.py /tmp/gxruntime
git -C /tmp/gxruntime diff --check

source /path/to/emsdk/emsdk_env.sh
emcmake cmake -S /tmp/gxruntime -B /tmp/gxruntime-web -G Ninja \
  -DBUILD_TESTING=OFF \
  -DGXRUNTIME_ENABLE_AURORA=ON \
  -DGXRUNTIME_ENABLE_AURORA_RECOMP=OFF \
  -DAURORA_ENABLE_RMLUI=OFF \
  -DAURORA_SDL3_LINKAGE=static
cmake --build /tmp/gxruntime-web --target aurora_core -j2
```

The CI runs this against the public pinned checkout. A successful `aurora_core`
build is a stronger milestone than the standalone probes: it means the actual
Aurora renderer/platform sources compile through Emscripten with the browser
WebGPU provider.

## Not covered yet

A green compile is not a first frame. Expected next work includes any additional
compile blockers exposed by the real tree, executable/browser shell integration,
GXRuntime guest memory, input, audio, persistence, and finally a real recompiled
game workload.

No game data is required by this target.
