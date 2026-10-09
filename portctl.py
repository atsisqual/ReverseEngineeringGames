#!/usr/bin/env python3
"""ReverseEngineeringGames toolchain helper.

This program only manages open-source tooling/scaffolding. It never downloads
commercial game content, firmware, keys, proprietary SDKs, or compiler binaries.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "toolchains.json"
TOOLS_DIR = ROOT / ".tools"
PORTS_DIR = ROOT / "ports"

PLATFORMS = {
    "source": "Portable source / matching decomp -> Emscripten",
    "n64": "N64Recomp or matching decomp -> browser runtime -> Emscripten",
    "gamecube": "DolRecomp/decomp-toolkit -> browser runtime -> Emscripten",
    "wii": "DolRecomp/decomp-toolkit -> browser runtime -> Emscripten",
    "ps1": "Matching decomp/source -> Emscripten",
    "ps2": "Matching decomp/source -> Emscripten",
    "psp": "Matching decomp/source -> Emscripten",
    "pc": "Portable/matching decomp -> Emscripten",
    "other": "Research first; source/recomp if available, emulator-core fallback otherwise",
}

REQUIRED = ["git", "python", "cmake", "ninja", "clang", "node"]
WEB_REQUIRED = ["emcc", "em++"]


def load_registry() -> list[dict]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        raise SystemExit("toolchains.json: 'tools' must be an array")
    return tools


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def command_path(name: str) -> str | None:
    candidates = [name]
    if os.name == "nt":
        if name == "python":
            candidates = ["python", "py"]
        if name == "ninja":
            candidates = ["ninja", "ninja.exe"]
    for candidate in candidates:
        value = shutil.which(candidate)
        if value:
            return value
    return None


def cmd_list(args: argparse.Namespace) -> int:
    tools = load_registry()
    groups: dict[str, list[str]] = {}
    for tool in tools:
        for group in tool["groups"]:
            groups.setdefault(group, []).append(tool["id"])

    print("Groups:")
    for group in sorted(groups):
        print(f"  {group:10} {', '.join(groups[group])}")

    print("\nTools:")
    for tool in tools:
        print(f"  {tool['id']:22} {tool['purpose']}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"Host: {platform.system()} {platform.machine()} / Python {platform.python_version()}")
    missing: list[str] = []

    for name in REQUIRED:
        found = command_path(name)
        print(f"{'OK' if found else 'MISSING':7} {name:8} {found or ''}")
        if not found:
            missing.append(name)

    print("\nWeb target:")
    web_missing = []
    for name in WEB_REQUIRED:
        found = command_path(name)
        print(f"{'OK' if found else 'MISSING':7} {name:8} {found or ''}")
        if not found:
            web_missing.append(name)

    if web_missing:
        print("\nEmscripten is not active in this shell.")
        print("Fetch emsdk with `python portctl.py fetch web`, then install/activate an SDK using upstream emsdk instructions.")

    if args.strict and (missing or web_missing):
        return 1
    return 0


def selected_tools(selector: str) -> list[dict]:
    tools = load_registry()
    if selector == "all":
        return tools

    exact = [tool for tool in tools if tool["id"] == selector]
    if exact:
        return exact

    grouped = [tool for tool in tools if selector in tool["groups"]]
    if grouped:
        return grouped

    known_groups = sorted({g for tool in tools for g in tool["groups"]})
    known_tools = sorted(tool["id"] for tool in tools)
    raise SystemExit(
        f"Unknown group/tool '{selector}'. Groups: {', '.join(known_groups)}. "
        f"Tools: {', '.join(known_tools)}"
    )


def cmd_fetch(args: argparse.Namespace) -> int:
    TOOLS_DIR.mkdir(exist_ok=True)
    for tool in selected_tools(args.selector):
        target = TOOLS_DIR / tool["id"]
        if target.exists():
            if not (target / ".git").exists():
                print(f"SKIP {tool['id']}: {target} exists but is not a git clone")
                continue
            if args.update:
                if args.dry_run:
                    print(f"WOULD UPDATE {tool['id']} in {target}")
                else:
                    run(["git", "fetch", "--prune"], cwd=target)
                    run(["git", "pull", "--ff-only"], cwd=target)
            else:
                print(f"EXISTS {tool['id']} -> {target}")
            continue

        cmd = ["git", "clone", "--recurse-submodules"]
        if args.depth:
            cmd += ["--depth", str(args.depth)]
        cmd += [tool["repo"], str(target)]

        if args.dry_run:
            print("WOULD RUN", " ".join(cmd))
        else:
            run(cmd)
    return 0


def render_port_readme(name: str, platform_id: str) -> str:
    route = PLATFORMS[platform_id]
    return f"""# {name}

Platform: `{platform_id}`

Route: {route}

## Inputs

Put user-owned original material under `original/`. That directory is ignored by Git.

Do not commit ROMs, disc images, keys, firmware, proprietary SDK files, extracted commercial assets or proprietary compilers.

## Milestones

- [ ] Identify exact game revision and hash the user-owned input.
- [ ] Establish deterministic native/emulated reference behavior.
- [ ] Pick source/decomp/static-recomp/emulator route.
- [ ] Pin toolchain SHAs in `TOOLCHAIN.lock`.
- [ ] Produce a native build before touching browser-specific code.
- [ ] Compile CPU/game code to WebAssembly.
- [ ] Adapt renderer to WebGL2 and/or WebGPU.
- [ ] Adapt audio/input/filesystem/networking.
- [ ] Add deterministic frame/state validation.
- [ ] Add browser smoke test and document required HTTP headers.

Read `../../docs/WEB_TARGET.md` before implementing the browser host.
"""


def cmd_new(args: argparse.Namespace) -> int:
    platform_id = args.platform.lower()
    if platform_id not in PLATFORMS:
        raise SystemExit(f"Unsupported platform id. Choose one of: {', '.join(PLATFORMS)}")

    target = PORTS_DIR / args.name
    if target.exists():
        raise SystemExit(f"{target} already exists")

    (target / "original").mkdir(parents=True)
    (target / "src").mkdir()
    (target / "web").mkdir()
    (target / "tests").mkdir()

    (target / "README.md").write_text(render_port_readme(args.name, platform_id), encoding="utf-8")
    (target / ".gitignore").write_text(
        """original/
roms/
iso/
assets-original/
build/
build-web/
dist/
*.iso
*.wbfs
*.rvz
*.wad
*.rom
*.z64
*.n64
*.v64
""",
        encoding="utf-8",
    )
    (target / "TOOLCHAIN.lock").write_text(
        "# Record exact upstream repo URL + commit SHA here once chosen.\n",
        encoding="utf-8",
    )
    print(f"Created {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portctl",
        description="Toolchain manager/scaffolder for reverse-engineered browser game ports.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List tool groups and tools")
    p_list.set_defaults(func=cmd_list)

    p_doctor = sub.add_parser("doctor", help="Check host/browser build prerequisites")
    p_doctor.add_argument("--strict", action="store_true", help="Return non-zero if anything is missing")
    p_doctor.set_defaults(func=cmd_doctor)

    p_fetch = sub.add_parser("fetch", help="Clone/update an upstream tool or group under .tools/")
    p_fetch.add_argument("selector", help="Group (web/n64/gcwii/analysis/agents/pc/all) or tool id")
    p_fetch.add_argument("--update", action="store_true", help="Fast-forward existing clones")
    p_fetch.add_argument("--dry-run", action="store_true", help="Print git commands without running them")
    p_fetch.add_argument("--depth", type=int, default=0, help="Optional shallow clone depth")
    p_fetch.set_defaults(func=cmd_fetch)

    p_new = sub.add_parser("new", help="Scaffold a new per-game port workspace")
    p_new.add_argument("name", help="Directory name under ports/")
    p_new.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    p_new.set_defaults(func=cmd_new)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
