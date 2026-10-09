import importlib.util, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'tools'/'web_reference_audit.py'
spec=importlib.util.spec_from_file_location('web_reference_audit',PATH)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader
sys.modules[spec.name]=mod; spec.loader.exec_module(mod)

class AuditTests(unittest.TestCase):
    def test_all_patterns_found(self):
        target={'required_patterns':['Emscripten','Play.wasm']}
        with tempfile.TemporaryDirectory() as td:
            Path(td,'README.md').write_text('Emscripten emits Play.wasm',encoding='utf-8')
            self.assertTrue(all(mod.audit(target,Path(td)).values()))
    def test_missing_pattern_is_reported(self):
        target={'required_patterns':['COOP/COEP','missing marker']}
        with tempfile.TemporaryDirectory() as td:
            Path(td,'README.md').write_text('COOP/COEP',encoding='utf-8')
            r=mod.audit(target,Path(td))
            self.assertTrue(r['COOP/COEP']); self.assertFalse(r['missing marker'])
if __name__=='__main__': unittest.main()
