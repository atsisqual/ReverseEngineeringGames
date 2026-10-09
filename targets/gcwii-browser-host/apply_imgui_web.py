#!/usr/bin/env python3
"""Adapt Aurora's Dear ImGui WebGPU backend selection for Emscripten.

Dear ImGui's WebGPU backend deliberately requires *no* native-backend macro
when compiling for Emscripten. Aurora defines the Dawn macro both on the
imgui_backends target and in lib/imgui.cpp, so make those definitions native
only while leaving desktop behavior unchanged.
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

    aurora = root / "graphics" / "aurora"

    extern_cmake = aurora / "extern" / "CMakeLists.txt"
    replace_once(
        extern_cmake,
        """    target_compile_definitions(imgui_backends PRIVATE IMGUI_IMPL_WEBGPU_BACKEND_DAWN)\n    target_link_libraries(imgui_backends PRIVATE imgui ${AURORA_SDL3_TARGET} dawn::webgpu_dawn)\n""",
        """    # Dear ImGui selects Emscripten WebGPU automatically and rejects the\n    # native Dawn/WGPU backend macros on browser builds.\n    if (NOT EMSCRIPTEN)\n      target_compile_definitions(imgui_backends PRIVATE IMGUI_IMPL_WEBGPU_BACKEND_DAWN)\n    endif ()\n    target_link_libraries(imgui_backends PRIVATE imgui ${AURORA_SDL3_TARGET} dawn::webgpu_dawn)\n""",
    )

    imgui_cpp = aurora / "lib" / "imgui.cpp"
    replace_once(
        imgui_cpp,
        """#define IMGUI_IMPL_WEBGPU_BACKEND_DAWN\n#include \"backends/imgui_impl_sdl3.h\"\n""",
        """#ifndef __EMSCRIPTEN__\n#define IMGUI_IMPL_WEBGPU_BACKEND_DAWN\n#endif\n#include \"backends/imgui_impl_sdl3.h\"\n""",
    )

    print("Adapted Aurora ImGui WebGPU backend selection for Emscripten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
