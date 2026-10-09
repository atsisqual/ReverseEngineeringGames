#!/usr/bin/env python3
"""Verify that pinned web-emulation reference repositories still expose expected browser evidence."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST=ROOT/'targets'/'web-fallbacks'/'targets.json'
SKIP={'.git','node_modules','build','dist','.tools'}
TEXT={'.md','.txt','.c','.cc','.cpp','.h','.hpp','.js','.ts','.json','.yml','.yaml','.py','.cmake','.sh','.mk'}

def load_manifest(path:Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    return {item['id']:item for item in data['targets']}

def corpus(root:Path)->str:
    chunks=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if any(part in SKIP for part in rel.parts): continue
        if p.suffix.lower() not in TEXT and p.name not in {'README','README.md','Makefile','CMakeLists.txt'}: continue
        try:
            if p.stat().st_size>2_000_000: continue
            chunks.append(p.read_text(encoding='utf-8',errors='ignore'))
        except OSError: pass
    return '\n'.join(chunks)

def audit(target:dict, checkout:Path):
    text=corpus(checkout)
    found={pat: bool(re.search(re.escape(pat),text,re.I)) for pat in target['required_patterns']}
    return found

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('target_id')
    ap.add_argument('checkout',type=Path)
    ap.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST)
    args=ap.parse_args(argv)
    targets=load_manifest(args.manifest)
    if args.target_id not in targets: ap.error('unknown target: '+args.target_id)
    if not args.checkout.is_dir(): ap.error('not a directory: '+str(args.checkout))
    result=audit(targets[args.target_id],args.checkout)
    for pat,ok in result.items(): print(f"{'PASS' if ok else 'MISS':4} {pat}")
    missing=[p for p,ok in result.items() if not ok]
    if missing:
        print('\nMissing reference evidence: '+', '.join(missing))
        return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
