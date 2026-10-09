#!/usr/bin/env python3
"""Expose Aurora's real simple GX example as an Emscripten executable target.

The pinned GXRuntime root normally embeds Aurora as a subdirectory, so Aurora's
standalone examples are not created. For the browser bring-up, reuse the
upstream simple.c example and link it through the integrated gxruntime_aurora
target. This deliberately tests the final Emscripten link, not only static
libraries.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

PINNED_GXRUNTIME = "8a47b0e8ea7dfc39014a4cff4f7895d88494a611"


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

    path = root / "CMakeLists.txt"
    text = path.read_text(encoding="utf-8")
    old = """endif()\n\nif(BUILD_TESTING)\n"""
    new = """endif()\n\nif(EMSCRIPTEN AND GXRUNTIME_ENABLE_AURORA)\n    # Browser link smoke: use Aurora's real GX sample rather than a synthetic\n    # WebGPU probe, and link through the integrated GXRuntime Aurora backend.\n    add_executable(gxruntime_browser_smoke\n        graphics/aurora/examples/simple.c\n    )\n    target_link_libraries(gxruntime_browser_smoke PRIVATE gxruntime_aurora)\n    option(GXRUNTIME_BROWSER_SMOKE_LINK_O0\n        \"Link the browser smoke target at -O0 to isolate Binaryen post-link failures\" OFF)\n    if(GXRUNTIME_BROWSER_SMOKE_LINK_O0)\n        # Diagnostic only: compile the libraries normally, but make -O0 the last\n        # optimization flag at the final Emscripten link. This tells us whether\n        # the malformed module is tied to the -O3 Binaryen post-link pipeline.\n        target_link_options(gxruntime_browser_smoke PRIVATE \"-O0\")\n    endif()\n    set_target_properties(gxruntime_browser_smoke PROPERTIES SUFFIX \".html\")\nendif()\n\nif(BUILD_TESTING)\n"""
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected exactly one browser executable anchor")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

    print("Exposed real Aurora simple example as gxruntime_browser_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
