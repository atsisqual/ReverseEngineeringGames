#!/usr/bin/env python3
"""Backport Dear ImGui's Emdawnwebgpu compatibility into pinned Aurora.

Aurora pins Dear ImGui v1.91.9b. That backend already contains the modern Dawn
code paths Aurora needs, but its old preprocessor guard rejects defining the
Dawn backend under Emscripten. Dear ImGui fixed exactly that upstream on
2025-10-16 for Emscripten 4.0.10+ / --use-port=emdawnwebgpu.

Keep Aurora's existing IMGUI_IMPL_WEBGPU_BACKEND_DAWN definitions and patch only
the fetched backend guard during CMake configure, before imgui_backends builds.
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

    extern_cmake = root / "graphics" / "aurora" / "extern" / "CMakeLists.txt"
    replace_once(
        extern_cmake,
        """    FetchContent_MakeAvailable(imgui)\n\n    add_library(imgui STATIC\n""",
        """    FetchContent_MakeAvailable(imgui)\n\n    if (EMSCRIPTEN)\n      # Dear ImGui v1.91.9b predates Emdawnwebgpu support and rejects the\n      # Dawn backend macro under Emscripten. Backport the upstream 2025-10-16\n      # guard change so the existing Dawn code paths are selected.\n      set(_aurora_imgui_wgpu_cpp \"${imgui_SOURCE_DIR}/backends/imgui_impl_wgpu.cpp\")\n      file(READ \"${_aurora_imgui_wgpu_cpp}\" _aurora_imgui_wgpu_source)\n      set(_aurora_imgui_wgpu_old [=[\n// When targeting native platforms (i.e. NOT emscripten), one of IMGUI_IMPL_WEBGPU_BACKEND_DAWN\n// or IMGUI_IMPL_WEBGPU_BACKEND_WGPU must be provided. See imgui_impl_wgpu.h for more details.\n#ifndef __EMSCRIPTEN__\n    #if defined(IMGUI_IMPL_WEBGPU_BACKEND_DAWN) == defined(IMGUI_IMPL_WEBGPU_BACKEND_WGPU)\n    #error exactly one of IMGUI_IMPL_WEBGPU_BACKEND_DAWN or IMGUI_IMPL_WEBGPU_BACKEND_WGPU must be defined!\n    #endif\n#else\n    #if defined(IMGUI_IMPL_WEBGPU_BACKEND_DAWN) || defined(IMGUI_IMPL_WEBGPU_BACKEND_WGPU)\n    #error neither IMGUI_IMPL_WEBGPU_BACKEND_DAWN nor IMGUI_IMPL_WEBGPU_BACKEND_WGPU may be defined if targeting emscripten!\n    #endif\n#endif\n\n#ifndef IMGUI_DISABLE\n#include \"imgui_impl_wgpu.h\"\n]=])\n      set(_aurora_imgui_wgpu_new [=[\n#ifndef IMGUI_DISABLE\n#include \"imgui_impl_wgpu.h\"\n\n#if defined(IMGUI_IMPL_WEBGPU_BACKEND_DAWN) == defined(IMGUI_IMPL_WEBGPU_BACKEND_WGPU)\n#error Exactly one of IMGUI_IMPL_WEBGPU_BACKEND_DAWN or IMGUI_IMPL_WEBGPU_BACKEND_WGPU must be defined!\n#endif\n]=])\n      string(FIND \"${_aurora_imgui_wgpu_source}\" \"${_aurora_imgui_wgpu_old}\" _aurora_imgui_wgpu_anchor)\n      if (_aurora_imgui_wgpu_anchor EQUAL -1)\n        message(FATAL_ERROR \"Dear ImGui WebGPU Emscripten compatibility anchor not found\")\n      endif ()\n      string(REPLACE \"${_aurora_imgui_wgpu_old}\" \"${_aurora_imgui_wgpu_new}\"\n        _aurora_imgui_wgpu_source \"${_aurora_imgui_wgpu_source}\")\n      file(WRITE \"${_aurora_imgui_wgpu_cpp}\" \"${_aurora_imgui_wgpu_source}\")\n      unset(_aurora_imgui_wgpu_anchor)\n      unset(_aurora_imgui_wgpu_old)\n      unset(_aurora_imgui_wgpu_new)\n      unset(_aurora_imgui_wgpu_source)\n      unset(_aurora_imgui_wgpu_cpp)\n    endif ()\n\n    add_library(imgui STATIC\n""",
    )

    print("Backported Dear ImGui Emdawnwebgpu compatibility into Aurora configure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
