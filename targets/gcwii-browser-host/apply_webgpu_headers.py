#!/usr/bin/env python3
"""Use Emdawn's C++ WebGPU header path on Emscripten.

Native Aurora includes Dawn's C++ wrapper as <dawn/webgpu_cpp.h>. Emscripten's
emdawnwebgpu port exposes the same wgpu C++ API as <webgpu/webgpu_cpp.h>.
Patch the two pinned Aurora headers that still hard-code the native path while
leaving native builds unchanged.
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
        raise SystemExit(f"{path}: expected exactly one patch anchor, found {count}")
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

    aurora = root / "graphics" / "aurora" / "lib"
    replacement = """#ifdef __EMSCRIPTEN__\n#include <webgpu/webgpu_cpp.h>\n#else\n#include <dawn/webgpu_cpp.h>\n#endif\n"""

    replace_once(aurora / "rmlui.hpp", "#include <dawn/webgpu_cpp.h>\n", replacement)
    replace_once(
        aurora / "rmlui" / "WebGPURenderInterface.hpp",
        "#include <dawn/webgpu_cpp.h>\n",
        replacement,
    )

    print("Adapted Aurora C++ WebGPU header paths for Emdawn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
