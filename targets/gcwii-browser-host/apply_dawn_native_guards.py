#!/usr/bin/env python3
"""Keep Dawn-native diagnostics/features out of the Emdawn browser build.

Aurora uses a few Dawn-native C++ extensions that are not part of the browser
WebGPU surface exposed by Emscripten's emdawnwebgpu port. Guard those native
helpers exactly as Aurora already guards its Dawn cache/toggle descriptors.
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

    gpu = root / "graphics" / "aurora" / "lib" / "webgpu" / "gpu.cpp"

    replace_once(
        gpu,
        """AuroraLogLevel wgpu_log_level(wgpu::LoggingType type) {\n  switch (type) {\n  case wgpu::LoggingType::Verbose:\n    return LOG_DEBUG;\n  case wgpu::LoggingType::Info:\n    return LOG_INFO;\n  case wgpu::LoggingType::Warning:\n    return LOG_WARNING;\n  case wgpu::LoggingType::Error:\n    return LOG_ERROR;\n  default:\n    return LOG_FATAL;\n  }\n}\n\nvoid wgpu_log(wgpu::LoggingType type, wgpu::StringView message) {\n  Log.report(wgpu_log_level(type), \"WebGPU message: {}\", message);\n}\n""",
        """#ifdef WEBGPU_DAWN\nAuroraLogLevel wgpu_log_level(wgpu::LoggingType type) {\n  switch (type) {\n  case wgpu::LoggingType::Verbose:\n    return LOG_DEBUG;\n  case wgpu::LoggingType::Info:\n    return LOG_INFO;\n  case wgpu::LoggingType::Warning:\n    return LOG_WARNING;\n  case wgpu::LoggingType::Error:\n    return LOG_ERROR;\n  default:\n    return LOG_FATAL;\n  }\n}\n\nvoid wgpu_log(wgpu::LoggingType type, wgpu::StringView message) {\n  Log.report(wgpu_log_level(type), \"WebGPU message: {}\", message);\n}\n#endif\n""",
    )

    replace_once(
        gpu,
        """      if (feature == wgpu::FeatureName::ImplicitDeviceSynchronization) {\n        // Dawn devices are not thread-safe by default, and Aurora touches the\n        // device from the app thread (plane_capture / efb_readback buffer\n        // creation + MapAsync with AllowSpontaneous callbacks) while\n        // render_worker Ticks/ProcessEvents. Without this, Dawn's\n        // DynamicUploader ring allocator corrupts under load (SIGABRT\n        // \"pointer being freed was not allocated\"; also the Metal\n        // encodeSignalEvent crash family — F-GXPO-2). This feature is Dawn's\n        // sanctioned multi-thread mode: every device API takes the device\n        // mutex.\n        requiredFeatures.push_back(feature);\n      }\n""",
        """#ifdef WEBGPU_DAWN\n      if (feature == wgpu::FeatureName::ImplicitDeviceSynchronization) {\n        // Dawn devices are not thread-safe by default, and Aurora touches the\n        // device from the app thread (plane_capture / efb_readback buffer\n        // creation + MapAsync with AllowSpontaneous callbacks) while\n        // render_worker Ticks/ProcessEvents. Without this, Dawn's\n        // DynamicUploader ring allocator corrupts under load (SIGABRT\n        // \"pointer being freed was not allocated\"; also the Metal\n        // encodeSignalEvent crash family — F-GXPO-2). This feature is Dawn's\n        // sanctioned multi-thread mode: every device API takes the device\n        // mutex.\n        requiredFeatures.push_back(feature);\n      }\n#endif\n""",
    )

    replace_once(
        gpu,
        """    g_device.SetLoggingCallback(wgpu_log);\n""",
        """#ifdef WEBGPU_DAWN\n    g_device.SetLoggingCallback(wgpu_log);\n#endif\n""",
    )

    print("Guarded Dawn-native WebGPU extensions from Emdawn browser build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
