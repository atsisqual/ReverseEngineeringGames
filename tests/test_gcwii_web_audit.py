import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'tools'/'gcwii_web_audit.py'
spec=importlib.util.spec_from_file_location('gcwii_web_audit',PATH)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=mod; spec.loader.exec_module(mod)

class Tests(unittest.TestCase):
    def test_foundation_without_web_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'README.md').write_text('DolRecomp game-agnostic runtime. AOT, no JIT. Dolphin interpreter lockstep.',encoding='utf-8')
            idx=mod.by_id(mod.audit(root))
            self.assertEqual(idx['dolrecomp-path'].status,'pass')
            self.assertEqual(idx['runtime-core'].status,'pass')
            self.assertEqual(idx['aot-no-jit'].status,'pass')
            self.assertEqual(idx['emscripten-build'].status,'miss')
            self.assertEqual(idx['browser-renderer'].status,'miss')

    def test_browser_fixture_passes_web_rules(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'CMakeLists.txt').write_text('DolRecomp GXRuntime AOT EMSCRIPTEN emcc WebGPU',encoding='utf-8')
            (root/'web.js').write_text('navigator.getGamepads(); AudioWorklet; OPFS; crossOriginIsolated',encoding='utf-8')
            (root/'server.md').write_text('Cross-Origin-Opener-Policy Cross-Origin-Embedder-Policy',encoding='utf-8')
            idx=mod.by_id(mod.audit(root))
            self.assertEqual(idx['emscripten-build'].status,'pass')
            self.assertEqual(idx['browser-renderer'].status,'pass')
            self.assertEqual(idx['cross-origin-isolation'].status,'pass')

if __name__=='__main__': unittest.main()
