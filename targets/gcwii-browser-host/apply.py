#!/usr/bin/env python3
"""Apply the first GXRuntime/Aurora browser-host patch to the pinned public tree.

The patch is intentionally exact-string based: if upstream changes the relevant
code, fail instead of silently applying a stale transformation.
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


def require_pinned_tree(root: Path) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True
    )
    actual = result.stdout.strip()
    if actual != PINNED_GXRUNTIME:
        raise SystemExit(f"GXRuntime pin mismatch: expected {PINNED_GXRUNTIME}, got {actual}")


def apply(root: Path) -> None:
    require_pinned_tree(root)
    aurora = root / "graphics" / "aurora"

    provider = aurora / "cmake" / "AuroraDawnProvider.cmake"
    replace_once(
        provider,
        "# When using a non-vendored Dawn, we don't get DAWN_ENABLE_* from its build.\n",
        """# Browser builds use Emscripten's official Emdawnwebgpu port rather than a\n# native Dawn package/library. Keep the same target names Aurora consumes so\n# the renderer remains unaware of the provider swap.\nif (EMSCRIPTEN)\n  add_library(aurora_emdawnwebgpu INTERFACE)\n  target_compile_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n  )\n  target_link_options(aurora_emdawnwebgpu INTERFACE\n    \"SHELL:--use-port=emdawnwebgpu\"\n    \"-sASYNCIFY=1\"\n  )\n  add_library(dawn::webgpu_dawn ALIAS aurora_emdawnwebgpu)\n\n  add_library(aurora_emdawnwebgpu_headers INTERFACE)\n  target_link_libraries(aurora_emdawnwebgpu_headers INTERFACE aurora_emdawnwebgpu)\n  add_library(dawn::dawncpp_headers ALIAS aurora_emdawnwebgpu_headers)\n\n  set(AURORA_DAWN_IS_SHARED FALSE PARENT_SCOPE)\n  message(STATUS \"aurora: Using Emscripten Emdawnwebgpu port\")\n  return()\nendif ()\n\n# When using a non-vendored Dawn, we don't get DAWN_ENABLE_* from its build.\n""",
    )

    core_cmake = aurora / "cmake" / "aurora_core.cmake"
    replace_once(
        core_cmake,
        """if (AURORA_ENABLE_GX)\n    target_compile_definitions(aurora_core PUBLIC AURORA_ENABLE_GX WEBGPU_DAWN)\n    target_sources(aurora_core PRIVATE\n            lib/webgpu/gpu.cpp\n            lib/webgpu/gpu_cache.cpp\n            lib/webgpu/gpu_prof.cpp\n            lib/dawn/BackendBinding.cpp\n            lib/dawn/TracyPlatform.cpp\n    )\n    if (CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL \"GNU\")\n        set_source_files_properties(lib/dawn/TracyPlatform.cpp PROPERTIES COMPILE_FLAGS -fno-rtti)\n    endif ()\n""",
        """if (AURORA_ENABLE_GX)\n    if (EMSCRIPTEN)\n        target_compile_definitions(aurora_core PUBLIC AURORA_ENABLE_GX WEBGPU_EMSCRIPTEN ENABLE_BACKEND_WEBGPU)\n        # Preserve Aurora's current synchronous initialization contract during\n        # browser bring-up while yielding to async WebGPU callbacks.\n        target_link_options(aurora_core PUBLIC \"-sASYNCIFY=1\")\n    else ()\n        target_compile_definitions(aurora_core PUBLIC AURORA_ENABLE_GX WEBGPU_DAWN)\n    endif ()\n    target_sources(aurora_core PRIVATE\n            lib/webgpu/gpu.cpp\n            lib/webgpu/gpu_cache.cpp\n            lib/webgpu/gpu_prof.cpp\n            lib/dawn/BackendBinding.cpp\n    )\n    if (NOT EMSCRIPTEN)\n        target_sources(aurora_core PRIVATE lib/dawn/TracyPlatform.cpp)\n        if (CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL \"GNU\")\n            set_source_files_properties(lib/dawn/TracyPlatform.cpp PROPERTIES COMPILE_FLAGS -fno-rtti)\n        endif ()\n    endif ()\n""",
    )

    binding = aurora / "lib" / "dawn" / "BackendBinding.cpp"
    replace_once(
        binding,
        """std::shared_ptr<wgpu::ChainedStruct> SetupWindowAndGetSurfaceDescriptor(SDL_Window* window) {\n#if defined(SDL_PLATFORM_MACOS) || defined(SDL_PLATFORM_IOS) || defined(SDL_PLATFORM_TVOS)\n""",
        """std::shared_ptr<wgpu::ChainedStruct> SetupWindowAndGetSurfaceDescriptor(SDL_Window* window) {\n#if defined(__EMSCRIPTEN__)\n  (void)window;\n  auto desc = std::make_shared<wgpu::EmscriptenSurfaceSourceCanvasHTMLSelector>();\n  desc->selector = \"#canvas\";\n  return desc;\n#elif defined(SDL_PLATFORM_MACOS) || defined(SDL_PLATFORM_IOS) || defined(SDL_PLATFORM_TVOS)\n""",
    )

    gpu = aurora / "lib" / "webgpu" / "gpu.cpp"
    replace_once(
        gpu,
        """#ifdef WEBGPU_DAWN\n#include \"../dawn/BackendBinding.hpp\"\n#include \"../dawn/TracyPlatform.hpp\"\n#include <dawn/native/DawnNative.h>\n#endif\n""",
        """#if defined(WEBGPU_DAWN) || defined(WEBGPU_EMSCRIPTEN)\n#include \"../dawn/BackendBinding.hpp\"\n#endif\n#ifdef WEBGPU_DAWN\n#include \"../dawn/TracyPlatform.hpp\"\n#include <dawn/native/DawnNative.h>\n#endif\n#ifdef __EMSCRIPTEN__\n#include <emscripten/emscripten.h>\n#endif\n""",
    )

    replace_once(
        gpu,
        """    const std::array requiredInstanceFeatures{\n        wgpu::InstanceFeatureName::TimedWaitAny,\n    };\n    wgpu::InstanceDescriptor instanceDescriptor{\n        .requiredFeatureCount = requiredInstanceFeatures.size(),\n        .requiredFeatures = requiredInstanceFeatures.data(),\n    };\n""",
        """#ifdef __EMSCRIPTEN__\n    wgpu::InstanceDescriptor instanceDescriptor{};\n#else\n    const std::array requiredInstanceFeatures{\n        wgpu::InstanceFeatureName::TimedWaitAny,\n    };\n    wgpu::InstanceDescriptor instanceDescriptor{\n        .requiredFeatureCount = requiredInstanceFeatures.size(),\n        .requiredFeatures = requiredInstanceFeatures.data(),\n    };\n#endif\n""",
    )

    replace_once(
        gpu,
        """    const auto future = g_instance.RequestAdapter(\n        &options, wgpu::CallbackMode::WaitAnyOnly,\n""",
        """#ifdef __EMSCRIPTEN__\n    constexpr auto requestAdapterMode = wgpu::CallbackMode::AllowSpontaneous;\n#else\n    constexpr auto requestAdapterMode = wgpu::CallbackMode::WaitAnyOnly;\n#endif\n    const auto future = g_instance.RequestAdapter(\n        &options, requestAdapterMode,\n""",
    )
    replace_once(
        gpu,
        """    const auto status = g_instance.WaitAny(future, 5000000000);\n    if (status != wgpu::WaitStatus::Success) {\n      if (requestAdapterCallbackCompleted) {\n        Log.error(\"Failed to create adapter: wait status {}, request status {}, message: {}\",\n                  magic_enum::enum_name(status), magic_enum::enum_name(requestAdapterStatus), requestAdapterMessage);\n      } else {\n        Log.error(\"Failed to create adapter: wait status {}, request callback did not complete\",\n                  magic_enum::enum_name(status));\n      }\n      return false;\n    }\n""",
        """#ifdef __EMSCRIPTEN__\n    (void)future;\n    while (!requestAdapterCallbackCompleted) {\n      emscripten_sleep(0);\n    }\n#else\n    const auto status = g_instance.WaitAny(future, 5000000000);\n    if (status != wgpu::WaitStatus::Success) {\n      if (requestAdapterCallbackCompleted) {\n        Log.error(\"Failed to create adapter: wait status {}, request status {}, message: {}\",\n                  magic_enum::enum_name(status), magic_enum::enum_name(requestAdapterStatus), requestAdapterMessage);\n      } else {\n        Log.error(\"Failed to create adapter: wait status {}, request callback did not complete\",\n                  magic_enum::enum_name(status));\n      }\n      return false;\n    }\n#endif\n""",
    )

    replace_once(
        gpu,
        """    const auto future =\n        g_adapter.RequestDevice(&deviceDescriptor, wgpu::CallbackMode::WaitAnyOnly,\n                                [](wgpu::RequestDeviceStatus status, wgpu::Device device, wgpu::StringView message) {\n                                  if (status == wgpu::RequestDeviceStatus::Success) {\n                                    g_device = std::move(device);\n                                  } else {\n                                    Log.warn(\"Device request failed: {}\", message);\n                                  }\n                                });\n    const auto status = g_instance.WaitAny(future, 5000000000);\n    if (status != wgpu::WaitStatus::Success) {\n      Log.error(\"Failed to create device: {}\", magic_enum::enum_name(status));\n      return false;\n    }\n""",
        """#ifdef __EMSCRIPTEN__\n    bool requestDeviceCallbackCompleted = false;\n    g_adapter.RequestDevice(\n        &deviceDescriptor, wgpu::CallbackMode::AllowSpontaneous,\n        [&](wgpu::RequestDeviceStatus status, wgpu::Device device, wgpu::StringView message) {\n          if (status == wgpu::RequestDeviceStatus::Success) {\n            g_device = std::move(device);\n          } else {\n            Log.warn(\"Device request failed: {}\", message);\n          }\n          requestDeviceCallbackCompleted = true;\n        });\n    while (!requestDeviceCallbackCompleted) {\n      emscripten_sleep(0);\n    }\n#else\n    const auto future =\n        g_adapter.RequestDevice(&deviceDescriptor, wgpu::CallbackMode::WaitAnyOnly,\n                                [](wgpu::RequestDeviceStatus status, wgpu::Device device, wgpu::StringView message) {\n                                  if (status == wgpu::RequestDeviceStatus::Success) {\n                                    g_device = std::move(device);\n                                  } else {\n                                    Log.warn(\"Device request failed: {}\", message);\n                                  }\n                                });\n    const auto status = g_instance.WaitAny(future, 5000000000);\n    if (status != wgpu::WaitStatus::Success) {\n      Log.error(\"Failed to create device: {}\", magic_enum::enum_name(status));\n      return false;\n    }\n#endif\n""",
    )

    print("Applied GXRuntime browser-host patch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tree", type=Path, help="Pinned GXRuntime checkout")
    args = parser.parse_args()
    apply(args.tree.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
