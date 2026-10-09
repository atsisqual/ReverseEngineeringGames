#!/usr/bin/env python3
"""Make the transitional Emscripten Asyncify bridge switchable.

The browser-host patch currently uses emscripten_sleep() to preserve Aurora's
synchronous initialization API while WebGPU adapter/device requests complete.
That requires -sASYNCIFY=1.  Keep that behavior as the default, but expose a
CMake option so CI can perform an otherwise identical final-link probe with
Asyncify disabled and isolate toolchain/finalizer failures.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

PINNED_GXRUNTIME = "8a47b0e8ea7dfc39014a4cff4f7895d88494a611"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one post-patch anchor, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path)
    args = parser.parse_args()
    root = args.tree.resolve()

    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
    ).stdout.strip()
    if actual != PINNED_GXRUNTIME:
        raise SystemExit(f"GXRuntime pin mismatch: expected {PINNED_GXRUNTIME}, got {actual}")

    aurora = root / "graphics" / "aurora"

    provider = aurora / "cmake" / "AuroraDawnProvider.cmake"
    replace_once(
        provider,
        """if (EMSCRIPTEN)\n  add_library(aurora_emdawnwebgpu INTERFACE)\n  target_compile_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n  )\n  target_link_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n    \"-sASYNCIFY=1\"\n  )\n""",
        """if (EMSCRIPTEN)\n  option(AURORA_EMSCRIPTEN_ASYNCIFY\n    \"Use Asyncify for Aurora's transitional synchronous WebGPU bootstrap\" ON)\n  add_library(aurora_emdawnwebgpu INTERFACE)\n  target_compile_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n  )\n  target_link_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n  )\n  if (AURORA_EMSCRIPTEN_ASYNCIFY)\n    target_link_options(aurora_emdawnwebgpu INTERFACE \"-sASYNCIFY=1\")\n  endif ()\n""",
    )

    core = aurora / "cmake" / "aurora_core.cmake"
    replace_once(
        core,
        """        # Preserve Aurora's current synchronous initialization contract during\n        # browser bring-up while yielding to async WebGPU callbacks.\n        target_link_options(aurora_core PUBLIC \"-sASYNCIFY=1\")\n""",
        """        # Preserve Aurora's current synchronous initialization contract during\n        # browser bring-up while yielding to async WebGPU callbacks. CI can\n        # disable this transitional bridge to isolate final-link toolchain issues.\n        if (AURORA_EMSCRIPTEN_ASYNCIFY)\n            target_link_options(aurora_core PUBLIC \"-sASYNCIFY=1\")\n        endif ()\n""",
    )

    print("Made Aurora Emscripten Asyncify bridge switchable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
