#!/usr/bin/env python3
"""Toolchain manager and route resolver for reverse-engineered browser game ports."""
from __future__ import annotations
import argparse, json, os, platform, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REGISTRY=ROOT/'toolchains.json'; ROUTES=ROOT/'routes.json'; TOOLS=ROOT/'.tools'; PORTS=ROOT/'ports'
PLATFORMS={
 'source':'Portable source / matching decomp -> Emscripten',
 'n64':'N64Recomp/matching decomp first; N64Wasm fallback',
 'gamecube':'DolRecomp + GXRuntime/ModernGekko; browser host still engineering work',
 'wii':'DolRecomp + GXRuntime/ModernGekko; browser host still engineering work',
 'ps1':'RetroArch Emscripten + browser-capable PS1 core, or source/decomp',
 'ps2':'Play! official experimental browser build; source/decomp when available',
 'psp':'PPSSPP WebAssembly community route; source/decomp when available',
 'nes':'RetroArch Web Player + compatible NES core','snes':'RetroArch Web Player + compatible SNES core',
 'gba':'RetroArch Web Player + compatible GB/GBC/GBA core','genesis':'RetroArch Web Player + compatible Sega core',
 'pc':'Portable/matching decomp -> Emscripten','pc32':'Older Win32: matching decomp/static recomp',
 'other':'Research first; source/recomp if available, emulator-core fallback otherwise'}
REQUIRED=['git','python','cmake','ninja','clang','node']; WEB_REQUIRED=['emcc','em++']

def load_json(path): return json.loads(path.read_text(encoding='utf-8'))
def tools():
 data=load_json(REGISTRY); out=data.get('tools',[])
 if not isinstance(out,list): raise SystemExit("toolchains.json: 'tools' must be an array")
 return out
def route_data():
 data=load_json(ROUTES)
 if not isinstance(data.get('routes'),dict) or not isinstance(data.get('aliases'),dict): raise SystemExit("routes.json must contain routes and aliases")
 return data
def resolve_route(name):
 data=route_data(); requested=name.strip().lower(); canonical=data['aliases'].get(requested,requested)
 if canonical not in data['routes']: canonical='other'
 out=dict(data['routes'][canonical]); out.update(platform=canonical,requested=requested); return out

def run(cmd,cwd=None): print('+',' '.join(cmd)); subprocess.run(cmd,cwd=cwd,check=True)
def which(name):
 names=[name]
 if os.name=='nt' and name=='python': names=['python','py']
 if os.name=='nt' and name=='ninja': names=['ninja','ninja.exe']
 return next((p for n in names if (p:=shutil.which(n))),None)

def cmd_list(_):
 groups={}
 for t in tools():
  for g in t['groups']: groups.setdefault(g,[]).append(t['id'])
 print('Groups:')
 for g in sorted(groups): print(f'  {g:22} {", ".join(groups[g])}')
 print('\nTools:')
 for t in tools(): print(f"  {t['id']:24} {t['purpose']}")
 return 0
def cmd_route(a):
 r=resolve_route(a.platform)
 if a.json: print(json.dumps(r,indent=2)); return 0
 print(f"Platform: {r['platform']}")
 if r['requested']!=r['platform']: print(f"Requested: {r['requested']}")
 print(f"Primary:  {r['primary']}\nStatus:   {r['status']}\nTools:    {', '.join(r.get('tools',[])) or '-'}\nFallback: {', '.join(r.get('fallback',[])) or '-'}\n\n{r['summary']}")
 return 0
def cmd_doctor(a):
 print(f'Host: {platform.system()} {platform.machine()} / Python {platform.python_version()}'); missing=[]
 for n in REQUIRED:
  p=which(n); print(f"{'OK' if p else 'MISSING':7} {n:8} {p or ''}"); missing += ([] if p else [n])
 print('\nWeb target:'); web=[]
 for n in WEB_REQUIRED:
  p=which(n); print(f"{'OK' if p else 'MISSING':7} {n:8} {p or ''}"); web += ([] if p else [n])
 if web: print('\nEmscripten is not active. Fetch `web`, install/activate emsdk, then rerun doctor.')
 return 1 if a.strict and (missing or web) else 0
def selected(selector):
 ts=tools()
 if selector=='all': return ts
 exact=[t for t in ts if t['id']==selector]
 if exact: return exact
 grouped=[t for t in ts if selector in t['groups']]
 if grouped: return grouped
 raise SystemExit(f"Unknown group/tool '{selector}'. Run `python portctl.py list`.")
def cmd_fetch(a):
 TOOLS.mkdir(exist_ok=True)
 for t in selected(a.selector):
  dst=TOOLS/t['id']
  if dst.exists():
   if not (dst/'.git').exists(): print(f"SKIP {t['id']}: {dst} is not a git clone"); continue
   if a.update:
    if a.dry_run: print(f"WOULD UPDATE {t['id']} in {dst}")
    else: run(['git','fetch','--prune'],dst); run(['git','pull','--ff-only'],dst)
   else: print(f"EXISTS {t['id']} -> {dst}")
   continue
  cmd=['git','clone','--recurse-submodules']+(['--depth',str(a.depth)] if a.depth else [])+[t['repo'],str(dst)]
  print('WOULD RUN',' '.join(cmd)) if a.dry_run else run(cmd)
 return 0
def render_readme(name,pid):
 r=resolve_route(pid if pid in route_data()['routes'] else 'other')
 return f'''# {name}\n\nPlatform: `{pid}`\n\nRoute: {PLATFORMS[pid]}\n\nRegistry: `{r['primary']}` ({r['status']})  \nTools: {', '.join(r.get('tools',[])) or 'research first'}  \nFallback: {', '.join(r.get('fallback',[])) or 'none recorded'}\n\n## Inputs\n\nPut user-owned original material under `original/`. Do not commit ROMs, disc images, keys, firmware, proprietary SDK files or extracted commercial assets.\n\n## Milestones\n\n- [ ] Identify exact revision and hash input.\n- [ ] Establish deterministic reference behavior.\n- [ ] Pick source/decomp/static-recomp/emulator route.\n- [ ] Pin upstream SHAs in `TOOLCHAIN.lock`.\n- [ ] Produce reference/native build.\n- [ ] Compile CPU/game/core code to WebAssembly.\n- [ ] Adapt renderer, audio, input, filesystem and networking.\n- [ ] Add deterministic state/frame validation and browser smoke tests.\n\nRead `../../docs/WEB_TARGET.md`.\n'''
def cmd_new(a):
 pid=a.platform.lower(); dst=PORTS/a.name
 if dst.exists(): raise SystemExit(f'{dst} already exists')
 for d in ['original','src','web','tests']: (dst/d).mkdir(parents=True,exist_ok=True)
 (dst/'README.md').write_text(render_readme(a.name,pid),encoding='utf-8')
 (dst/'.gitignore').write_text('original/\nroms/\niso/\nassets-original/\nbuild/\nbuild-web/\ndist/\n*.iso\n*.wbfs\n*.rvz\n*.wad\n*.rom\n*.z64\n*.n64\n*.v64\n',encoding='utf-8')
 (dst/'TOOLCHAIN.lock').write_text('# Record exact upstream repo URL + commit SHA here once chosen.\n',encoding='utf-8')
 print(f'Created {dst}'); return 0

def parser():
 p=argparse.ArgumentParser(prog='portctl',description='Toolchain manager/scaffolder for reverse-engineered browser game ports.'); s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('list'); q.set_defaults(func=cmd_list)
 q=s.add_parser('route'); q.add_argument('platform'); q.add_argument('--json',action='store_true'); q.set_defaults(func=cmd_route)
 q=s.add_parser('doctor'); q.add_argument('--strict',action='store_true'); q.set_defaults(func=cmd_doctor)
 q=s.add_parser('fetch'); q.add_argument('selector'); q.add_argument('--update',action='store_true'); q.add_argument('--dry-run',action='store_true'); q.add_argument('--depth',type=int,default=0); q.set_defaults(func=cmd_fetch)
 q=s.add_parser('new'); q.add_argument('name'); q.add_argument('--platform',required=True,choices=sorted(PLATFORMS)); q.set_defaults(func=cmd_new)
 return p
def main():
 p=parser(); a=p.parse_args(); return int(a.func(a))
if __name__=='__main__': raise SystemExit(main())
