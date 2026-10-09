#!/usr/bin/env python3
"""Static readiness audit for N64Recomp-style browser ports.

The audit is intentionally heuristic: it looks for concrete browser integration
markers in source/config files and reports evidence paths. It never needs a ROM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
    ".cmake", ".txt", ".md", ".py", ".js", ".mjs", ".cjs", ".html",
    ".toml", ".yaml", ".yml", ".json", ".patch", ".diff", ".sh",
}
SKIP_DIRS = {".git", "build", "build-wasm", "build-web", "dist", "node_modules", ".tools"}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    patterns: tuple[str, ...]
    critical: bool = False


@dataclass
class Result:
    rule_id: str
    description: str
    status: str
    critical: bool
    evidence: list[str]


RULES = (
    Rule(
        "emscripten-build",
        "Build system has an Emscripten/WebAssembly path",
        (r"\bEMSCRIPTEN\b", r"emcmake", r"-sUSE_SDL=2", r"\.wasm\b"),
        True,
    ),
    Rule(
        "runtime-wasm-compat",
        "Runtime contains Emscripten-specific compatibility work",
        (r"__EMSCRIPTEN__", r"\bIS_WASM\b", r"live_generator_wasm", r"WASM.*recomp"),
        True,
    ),
    Rule(
        "wasm-threads",
        "WebAssembly threads/pthread configuration is present",
        (r"-pthread", r"PTHREAD_POOL_SIZE", r"USE_PTHREADS", r"SharedArrayBuffer"),
        True,
    ),
    Rule(
        "wasm-memory",
        "Wasm memory strategy is explicit",
        (r"INITIAL_MEMORY", r"MAXIMUM_MEMORY", r"ALLOW_MEMORY_GROWTH", r"SharedArrayBuffer"),
        True,
    ),
    Rule(
        "browser-renderer",
        "A browser renderer path (WebGL/WebGPU) exists",
        (r"WebGL2", r"web_renderer", r"emscripten_webgl", r"WebGPU", r"wgpu"),
        True,
    ),
    Rule(
        "browser-input",
        "Browser keyboard/gamepad input is wired",
        (r"getGamepads", r"Gamepad", r"input_set", r"ogre_input", r"EMSCRIPTEN.*input"),
    ),
    Rule(
        "browser-audio",
        "Browser audio path exists",
        (r"AudioWorklet", r"AudioContext", r"audio-worklet", r"queue_samples", r"WebAudio"),
    ),
    Rule(
        "persistent-storage",
        "Browser persistence is implemented or configured",
        (r"IDBFS", r"OPFS", r"WasmFS", r"syncfs", r"indexedDB"),
    ),
    Rule(
        "cross-origin-isolation",
        "COOP/COEP headers for pthreads are documented or served",
        (r"Cross-Origin-Opener-Policy", r"Cross-Origin-Embedder-Policy", r"crossOriginIsolated"),
        True,
    ),
    Rule(
        "rom-user-supplied",
        "Project expects user-supplied ROM/game data instead of vendoring it",
        (r"supply your own.*ROM", r"user[- ]owned.*ROM", r"ROM.*gitignored", r"No game data is included"),
    ),
    Rule(
        "browser-smoke-test",
        "Automated browser/headless test or probe exists",
        (r"playwright", r"headless.*Chrome", r"chromium", r"browser.*probe", r"screenshot"),
    ),
)


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"CMakeLists.txt", "Makefile"}:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        yield path.relative_to(root).as_posix(), text


def audit(root: Path) -> list[Result]:
    files = list(iter_text_files(root))
    results: list[Result] = []
    for rule in RULES:
        evidence: list[str] = []
        compiled = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in rule.patterns]
        for rel, text in files:
            if any(rx.search(text) for rx in compiled):
                evidence.append(rel)
                if len(evidence) >= 5:
                    break
        status = "pass" if evidence else ("miss" if rule.critical else "warn")
        results.append(Result(rule.rule_id, rule.description, status, rule.critical, evidence))
    return results


def summary(results: list[Result]) -> dict[str, int]:
    return {
        "pass": sum(r.status == "pass" for r in results),
        "warn": sum(r.status == "warn" for r in results),
        "miss": sum(r.status == "miss" for r in results),
        "critical_miss": sum(r.critical and r.status == "miss" for r in results),
        "total": len(results),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit an N64Recomp-style tree for browser-port readiness")
    parser.add_argument("path", type=Path, help="Project tree to inspect")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Fail if any critical rule is missing")
    args = parser.parse_args(argv)

    root = args.path.resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    results = audit(root)
    stats = summary(results)
    if args.json:
        print(json.dumps({"path": str(root), "summary": stats, "results": [asdict(r) for r in results]}, indent=2))
    else:
        for result in results:
            marker = {"pass": "PASS", "warn": "WARN", "miss": "MISS"}[result.status]
            evidence = ", ".join(result.evidence) if result.evidence else "no evidence"
            print(f"{marker:4} {result.rule_id:24} {result.description} [{evidence}]")
        print(
            f"\n{stats['pass']}/{stats['total']} checks have evidence; "
            f"critical missing: {stats['critical_miss']}"
        )

    if args.strict and stats["critical_miss"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
