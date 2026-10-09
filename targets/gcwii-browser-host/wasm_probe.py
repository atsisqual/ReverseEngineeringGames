#!/usr/bin/env python3
"""Locate a byte offset inside a WebAssembly binary without decoding opcodes.

This is intentionally tiny and dependency-free. It parses the module section
layout and, for the code section, function-body size records. That is enough to
turn Binaryen errors such as `at 0:2771963` into a concrete section/body index
for follow-up symbol isolation.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SECTION_NAMES = {
    0: "custom",
    1: "type",
    2: "import",
    3: "function",
    4: "table",
    5: "memory",
    6: "global",
    7: "export",
    8: "start",
    9: "element",
    10: "code",
    11: "data",
    12: "data_count",
    13: "tag",
}


def read_u32_leb(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    start = pos
    while True:
        if pos >= len(data):
            raise ValueError(f"truncated LEB128 at {start}")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            return value, pos
        shift += 7
        if shift > 35:
            raise ValueError(f"invalid u32 LEB128 at {start}")


def locate(path: Path, offset: int) -> str:
    data = path.read_bytes()
    if len(data) < 8 or data[:4] != b"\0asm" or data[4:8] != b"\x01\0\0\0":
        raise ValueError("not a WebAssembly 1.0 binary")
    if offset < 0 or offset >= len(data):
        raise ValueError(f"offset {offset} outside file (size={len(data)})")

    pos = 8
    section_index = 0
    while pos < len(data):
        header_start = pos
        section_id = data[pos]
        pos += 1
        size, payload_start = read_u32_leb(data, pos)
        payload_end = payload_start + size
        if payload_end > len(data):
            raise ValueError(
                f"section {section_index} payload exceeds file: "
                f"{payload_start}+{size}>{len(data)}"
            )
        if header_start <= offset < payload_end:
            name = SECTION_NAMES.get(section_id, f"unknown({section_id})")
            base = (
                f"offset={offset} file_size={len(data)} section_index={section_index} "
                f"section_id={section_id} section={name} "
                f"section_range=[{header_start},{payload_end}) "
                f"payload_range=[{payload_start},{payload_end})"
            )
            if section_id != 10 or offset < payload_start:
                return base

            count, body_pos = read_u32_leb(data, payload_start)
            for body_index in range(count):
                size_pos = body_pos
                body_size, body_start = read_u32_leb(data, body_pos)
                body_end = body_start + body_size
                if body_end > payload_end:
                    raise ValueError(
                        f"code body {body_index} exceeds code section: "
                        f"{body_start}+{body_size}>{payload_end}"
                    )
                if size_pos <= offset < body_end:
                    return (
                        base
                        + f" code_body_count={count} code_body_index={body_index} "
                        + f"body_size_field={size_pos} body_range=[{body_start},{body_end}) "
                        + f"offset_in_body={offset - body_start}"
                    )
                body_pos = body_end
            return base + f" code_body_count={count} body=not-found"
        pos = payload_end
        section_index += 1

    raise ValueError(f"offset {offset} was not contained in any section")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wasm", type=Path)
    parser.add_argument("--offset", type=int, required=True)
    args = parser.parse_args()
    print(locate(args.wasm, args.offset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
