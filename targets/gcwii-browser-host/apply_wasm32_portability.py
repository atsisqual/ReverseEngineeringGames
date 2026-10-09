#!/usr/bin/env python3
"""Apply wasm32 size-safety fixes to pinned Aurora sources.

Aurora calculates DDS payload sizes in uint64_t, while size_t is 32-bit in the
wasm32 Emscripten ABI. Validate the payload against both the input span and the
addressable size_t range before narrowing for ByteBuffer/memcpy.
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

    dds = root / "graphics" / "aurora" / "lib" / "gfx" / "dds_io.cpp"
    replace_once(
        dds,
        """#include <filesystem>\n#include <fstream>\n""",
        """#include <filesystem>\n#include <fstream>\n#include <limits>\n""",
    )
    replace_once(
        dds,
        """  const auto expectedSize = calc_texture_size(parsedLayout->format, header->width, header->height, *mipCount);\n  if (expectedSize == 0 || parsedLayout->dataOffset + expectedSize > bytes.size()) {\n    return std::nullopt;\n  }\n\n  ByteBuffer data{expectedSize};\n  std::memcpy(data.data(), bytes.data() + parsedLayout->dataOffset, expectedSize);\n""",
        """  const auto expectedSize = calc_texture_size(parsedLayout->format, header->width, header->height, *mipCount);\n  if (expectedSize == 0 || parsedLayout->dataOffset > bytes.size() ||\n      expectedSize > static_cast<uint64_t>(bytes.size() - parsedLayout->dataOffset) ||\n      expectedSize > static_cast<uint64_t>(std::numeric_limits<size_t>::max())) {\n    return std::nullopt;\n  }\n\n  const auto dataSize = static_cast<size_t>(expectedSize);\n  ByteBuffer data{dataSize};\n  std::memcpy(data.data(), bytes.data() + parsedLayout->dataOffset, dataSize);\n""",
    )

    print("Applied wasm32 DDS size-safety fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
