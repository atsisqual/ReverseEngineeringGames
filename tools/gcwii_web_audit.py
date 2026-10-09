#!/usr/bin/env python3
"""Audit GameCube/Wii static-recompilation projects for browser readiness."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

TEXT_SUFFIXES = {'.c','.cc','.cpp','.cxx','.h','.hh','.hpp','.cmake','.txt','.md','.py','.js','.html','.toml','.yaml','.yml','.json','.sh'}
SKIP_DIRS = {'.git','build','dist','node_modules','.tools'}

@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    patterns: tuple[str, ...]
    foundation: bool = False

@dataclass
class Result:
    rule_id: str
    description: str
    status: str
    foundation: bool
    evidence: list[str]

RULES = (
    Rule('dolrecomp-path','Static PPC recompilation path is present',(r'DolRecomp', r'static recompil'),True),
    Rule('runtime-core','A game/runtime layer exists around generated PPC code',(r'GXRuntime',r'ModernGekko',r'game-agnostic runtime',r'platform backend'),True),
    Rule('aot-no-jit','AOT/no-JIT execution is an explicit goal',(r'no JIT',r'without.*JIT',r'AOT',r'statically recompiled'),True),
    Rule('correctness-oracle','Interpreter/lockstep/reference validation exists',(r'lockstep',r'Dolphin.*interpreter',r'parity',r'0 divergences')),
    Rule('emscripten-build','Build system has a WebAssembly/Emscripten target',(r'\bEMSCRIPTEN\b',r'emcmake',r'emcc',r'\.wasm\b')),
    Rule('webgpu-renderer-core','Renderer core already targets WebGPU/Dawn or equivalent',(r'WebGPU',r'\bwgpu\b',r'\bDawn\b')),
    Rule('browser-surface','Renderer is wired to a browser canvas/WebGPU surface',(r'navigator\.gpu',r'emscripten_webgpu',r'emscripten_webgl',r'emscripten_set_canvas',r'HTMLCanvasElement')),
    Rule('browser-input','Browser input backend exists',(r'navigator\.getGamepads',r'GamepadEvent',r'emscripten.*keyboard',r'EMSCRIPTEN.*input')),
    Rule('browser-audio','Browser audio backend exists',(r'AudioWorklet',r'AudioContext',r'WebAudio')),
    Rule('browser-storage','Browser persistence/filesystem exists',(r'IDBFS',r'OPFS',r'WasmFS',r'indexedDB',r'syncfs')),
    Rule('cross-origin-isolation','Threaded web host documents/serves COOP/COEP',(r'Cross-Origin-Opener-Policy',r'Cross-Origin-Embedder-Policy',r'crossOriginIsolated')),
    Rule('user-supplied-game','Game/disc content is user supplied',(r'user[- ]owned.*(?:ISO|disc|game)',r'bring your own.*(?:ISO|disc|game)',r'no game data')),
)

def iter_text(root: Path):
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'CMakeLists.txt','Makefile'}:
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            yield rel.as_posix(), path.read_text(encoding='utf-8',errors='ignore')
        except OSError:
            continue

def audit(root: Path) -> list[Result]:
    files = list(iter_text(root))
    out=[]
    for rule in RULES:
        regexes=[re.compile(p,re.I|re.S) for p in rule.patterns]
        evidence=[]
        for rel,text in files:
            if any(rx.search(text) for rx in regexes):
                evidence.append(rel)
                if len(evidence)>=5:
                    break
        out.append(Result(rule.rule_id,rule.description,'pass' if evidence else 'miss',rule.foundation,evidence))
    return out

def by_id(results):
    return {r.rule_id:r for r in results}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path)
    p.add_argument('--json',action='store_true')
    p.add_argument('--strict-foundation',action='store_true',help='fail if DolRecomp/runtime/AOT foundation evidence is missing')
    p.add_argument('--expect-missing',default='',help='comma-separated rule ids that must still be missing; useful for pinned gap targets')
    args=p.parse_args(argv)
    root=args.path.resolve()
    if not root.is_dir():
        p.error(f'not a directory: {root}')
    results=audit(root)
    index=by_id(results)
    expected=[x.strip() for x in args.expect_missing.split(',') if x.strip()]
    unknown=[x for x in expected if x not in index]
    if unknown:
        p.error('unknown rule id(s): '+', '.join(unknown))
    if args.json:
        print(json.dumps({'path':str(root),'results':[asdict(r) for r in results]},indent=2))
    else:
        for r in results:
            ev=', '.join(r.evidence) if r.evidence else 'no evidence'
            print(f"{r.status.upper():4} {r.rule_id:24} {r.description} [{ev}]")
    failures=[]
    if args.strict_foundation:
        failures += [r.rule_id for r in results if r.foundation and r.status!='pass']
    failures += [rid for rid in expected if index[rid].status!='miss']
    if failures:
        print('\nExpectation failure: '+', '.join(failures))
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
