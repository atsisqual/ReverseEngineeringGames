#!/usr/bin/env python3
"""Reproduce the public Ogre Battle 64 N64Recomp browser target.

Only open-source repositories are downloaded. The ROM is always supplied by the
user from a local path and is never uploaded anywhere by this script.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = json.loads((HERE / "target.json").read_text(encoding="utf-8"))
DEFAULT_WORKSPACE = HERE.parents[1] / ".work" / TARGET["id"]
N64_MAGIC = bytes.fromhex("80371240")


def say_command(cmd: list[str], cwd: Path | None = None) -> None:
    prefix = f"(cd {cwd} && " if cwd else ""
    suffix = ")" if cwd else ""
    print("+ " + prefix + " ".join(cmd) + suffix)


def run(cmd: list[str], cwd: Path | None = None, *, dry_run: bool = False, env: dict[str, str] | None = None) -> None:
    say_command(cmd, cwd)
    if not dry_run:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)


def git_apply_once(repo: Path, patch: Path, *, dry_run: bool) -> None:
    check_reverse = ["git", "apply", "--reverse", "--check", str(patch)]
    if not dry_run:
        already = subprocess.run(check_reverse, cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if already:
            print(f"= already applied: {patch.name}")
            return
    run(["git", "apply", str(patch)], cwd=repo, dry_run=dry_run)


def command(name: str) -> str | None:
    return shutil.which(name)


def doctor(require_regen: bool = False) -> int:
    required = ["git", "python3", "cmake", "make", "emcmake", "emcc"]
    if require_regen:
        required += ["mips-linux-gnu-as", "mips-linux-gnu-ld", "mips-linux-gnu-objcopy"]
    missing = []
    for name in required:
        found = command(name)
        print(f"{'OK' if found else 'MISSING':7} {name:22} {found or ''}")
        if not found:
            missing.append(name)
    if missing:
        print("\nMissing: " + ", ".join(missing))
        if "emcmake" in missing:
            print("Activate emsdk first (`source emsdk_env.sh`).")
        if require_regen and any(x.startswith("mips-linux-gnu-") for x in missing):
            print("Install a MIPS GNU binutils cross-toolchain before regeneration.")
        return 1
    return 0


def ensure_checkout(workspace: Path, *, dry_run: bool) -> Path:
    upstream = TARGET["upstream"]
    if not workspace.exists():
        workspace.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--recurse-submodules", upstream["repo"], str(workspace)], dry_run=dry_run)
    elif not (workspace / ".git").exists():
        raise SystemExit(f"workspace exists but is not a git checkout: {workspace}")

    if dry_run and not workspace.exists():
        return workspace

    run(["git", "fetch", "origin", upstream["commit"]], cwd=workspace, dry_run=dry_run)
    run(["git", "checkout", "--detach", upstream["commit"]], cwd=workspace, dry_run=dry_run)
    run(["git", "submodule", "update", "--init", "--recursive"], cwd=workspace, dry_run=dry_run)
    return workspace


def prepare_runtime(workspace: Path, *, dry_run: bool) -> None:
    runtime_cfg = TARGET["runtime"]
    runtime = workspace / "tools" / "N64ModernRuntime"
    if not runtime.exists():
        run(["git", "clone", runtime_cfg["repo"], str(runtime)], cwd=workspace, dry_run=dry_run)
    if not dry_run or runtime.exists():
        run(["git", "checkout", runtime_cfg["commit"]], cwd=runtime, dry_run=dry_run)
        run(["git", "submodule", "update", "--init", "--recursive"], cwd=runtime, dry_run=dry_run)
        git_apply_once(runtime, workspace / "patches" / "n64modernruntime-ob64.patch", dry_run=dry_run)
        git_apply_once(runtime / "N64Recomp", workspace / "patches" / "n64modernruntime-n64recomp.patch", dry_run=dry_run)


def prepare_recompiler(workspace: Path, *, dry_run: bool) -> None:
    cfg = TARGET["runtime"]
    recomp = workspace / "tools" / "N64Recomp"
    if not recomp.exists():
        run(["git", "clone", "--recurse-submodules", "https://github.com/N64Recomp/N64Recomp.git", str(recomp)], cwd=workspace, dry_run=dry_run)
    if not dry_run or recomp.exists():
        run(["git", "checkout", cfg["n64recomp_commit"]], cwd=recomp, dry_run=dry_run)
        run(["git", "submodule", "update", "--init", "--recursive"], cwd=recomp, dry_run=dry_run)
        git_apply_once(recomp, workspace / "patches" / "n64recomp-ob64.patch", dry_run=dry_run)
        run(["cmake", "-S", ".", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"], cwd=recomp, dry_run=dry_run)
        run(["cmake", "--build", "build", "--target", "N64RecompCLI", "RSPRecomp", "-j"], cwd=recomp, dry_run=dry_run)


def prepare_python_tools(workspace: Path, *, dry_run: bool) -> None:
    venv = workspace / "tools" / "venv"
    if not venv.exists():
        run(["python3", "-m", "venv", str(venv)], cwd=workspace, dry_run=dry_run)
    pip = venv / "bin" / "pip"
    if os.name == "nt":
        pip = venv / "Scripts" / "pip.exe"
    run([str(pip), "install", "splat64[mips]"], cwd=workspace, dry_run=dry_run)


def validate_rom(rom: Path) -> None:
    expected_size = int(TARGET["input"]["expected_size_bytes"])
    if not rom.is_file():
        raise SystemExit(f"ROM not found: {rom}")
    if rom.suffix.lower() != ".z64":
        raise SystemExit("This reproducible path currently requires a big-endian .z64 dump. Convert .n64/.v64 with the upstream tools first.")
    if rom.stat().st_size != expected_size:
        raise SystemExit(f"unexpected ROM size: {rom.stat().st_size} bytes (expected {expected_size})")
    with rom.open("rb") as fh:
        if fh.read(4) != N64_MAGIC:
            raise SystemExit("ROM does not have the N64 big-endian .z64 magic 80 37 12 40")


def stage_rom(workspace: Path, rom: Path, *, dry_run: bool) -> None:
    validate_rom(rom)
    dest = workspace / TARGET["input"]["staged_path"]
    print(f"ROM format/size OK. Upstream runtime will verify XXH3-64 {TARGET['input']['expected_xxh3_64']}.")
    print(f"+ copy {rom} -> {dest}")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rom, dest)


def regenerate(workspace: Path, *, dry_run: bool) -> None:
    run(["make", "regenerate"], cwd=workspace, dry_run=dry_run)


def build_web(workspace: Path, *, dry_run: bool) -> None:
    env = os.environ.copy()
    env.setdefault("EM_CACHE", str(workspace / ".cache" / "emscripten"))
    if not dry_run:
        Path(env["EM_CACHE"]).mkdir(parents=True, exist_ok=True)
    run(["emcmake", "cmake", "-S", "app", "-B", "build-wasm", "-DCMAKE_BUILD_TYPE=Release"], cwd=workspace, dry_run=dry_run, env=env)
    run(["cmake", "--build", "build-wasm", "-j"], cwd=workspace, dry_run=dry_run, env=env)


def serve(workspace: Path, port: int, *, dry_run: bool) -> None:
    run(["python3", "debug/server.py", "--port", str(port)], cwd=workspace, dry_run=dry_run)


def print_info() -> None:
    print(json.dumps(TARGET, indent=2))
    print("\nThis target is a public reference implementation. No ROM is included or downloaded.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--dry-run", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info")
    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("--regen", action="store_true", help="also require MIPS binutils used by make regenerate")
    sub.add_parser("clone")
    sub.add_parser("tools")
    p_rom = sub.add_parser("stage-rom")
    p_rom.add_argument("rom", type=Path)
    sub.add_parser("regenerate")
    sub.add_parser("build-web")
    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=int(TARGET["browser"]["default_port"]))
    p_all = sub.add_parser("all")
    p_all.add_argument("rom", type=Path)

    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()

    if args.command == "info":
        print_info()
        return 0
    if args.command == "doctor":
        return doctor(args.regen)
    if args.command == "clone":
        ensure_checkout(workspace, dry_run=args.dry_run)
        return 0
    if args.command == "tools":
        ensure_checkout(workspace, dry_run=args.dry_run)
        prepare_runtime(workspace, dry_run=args.dry_run)
        prepare_recompiler(workspace, dry_run=args.dry_run)
        prepare_python_tools(workspace, dry_run=args.dry_run)
        return 0
    if args.command == "stage-rom":
        if not workspace.exists() and not args.dry_run:
            raise SystemExit("clone the target first")
        stage_rom(workspace, args.rom.resolve(), dry_run=args.dry_run)
        return 0
    if args.command == "regenerate":
        regenerate(workspace, dry_run=args.dry_run)
        return 0
    if args.command == "build-web":
        build_web(workspace, dry_run=args.dry_run)
        return 0
    if args.command == "serve":
        serve(workspace, args.port, dry_run=args.dry_run)
        return 0
    if args.command == "all":
        if doctor(require_regen=True):
            return 1
        ensure_checkout(workspace, dry_run=args.dry_run)
        prepare_runtime(workspace, dry_run=args.dry_run)
        prepare_recompiler(workspace, dry_run=args.dry_run)
        prepare_python_tools(workspace, dry_run=args.dry_run)
        stage_rom(workspace, args.rom.resolve(), dry_run=args.dry_run)
        regenerate(workspace, dry_run=args.dry_run)
        build_web(workspace, dry_run=args.dry_run)
        print(f"\nBuild complete. Serve with: {sys.executable} {HERE / 'prepare.py'} --workspace {workspace} serve")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
