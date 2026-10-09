#!/usr/bin/env python3
"""Make Aurora's fetched support dependencies browser-safe for Emscripten.

A single browser Wasm module should not inherit Aurora's desktop default of
building fetched dependencies as shared libraries. wasm32 also has no host CPU
ISA variants for zlib-ng to select at runtime, so disable zlib-ng's runtime CPU
dispatch table. Keep the desktop policy unchanged.
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

    path = root / "graphics" / "aurora" / "extern" / "CMakeLists.txt"
    text = path.read_text(encoding="utf-8")
    old = """if (NOT DEFINED BUILD_SHARED_LIBS)\n  set(_USE_SHARED ON)\nelse ()\n  set(_USE_SHARED OFF)\nendif ()\n"""
    new = """if (EMSCRIPTEN)\n  # Browser builds are delivered as one Wasm module. Do not ask fetched\n  # dependencies such as zlib/libpng/zstd to produce Emscripten side modules.\n  set(BUILD_SHARED_LIBS OFF CACHE BOOL \"Build shared libraries\" FORCE)\n  set(_USE_SHARED OFF)\n\n  # zlib-ng's runtime dispatch table installs compare256_stub and other\n  # first-call trampolines. wasm32 has no native CPU ISA variants to select,\n  # and the generated compare256_stub currently produces malformed Wasm with\n  # Emscripten 6.0.12. Use zlib-ng's direct generic/native fallbacks instead.\n  set(WITH_RUNTIME_CPU_DETECTION OFF CACHE BOOL\n      \"Build zlib-ng with runtime detection of CPU architecture\" FORCE)\nelseif (NOT DEFINED BUILD_SHARED_LIBS)\n  set(_USE_SHARED ON)\nelse ()\n  set(_USE_SHARED OFF)\nendif ()\n"""
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected exactly one shared-policy anchor")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Forced Aurora browser dependencies static and disabled zlib-ng runtime CPU dispatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
