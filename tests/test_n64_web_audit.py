import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "n64_web_audit.py"
spec = importlib.util.spec_from_file_location("n64_web_audit", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class AuditTests(unittest.TestCase):
    def test_complete_fixture_passes_critical_rules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "CMakeLists.txt").write_text(
                "EMSCRIPTEN -pthread PTHREAD_POOL_SIZE INITIAL_MEMORY WebGL2 __EMSCRIPTEN__",
                encoding="utf-8",
            )
            (root / "web.js").write_text(
                "navigator.getGamepads(); new AudioContext(); IDBFS; syncfs; crossOriginIsolated; playwright",
                encoding="utf-8",
            )
            (root / "server.py").write_text(
                "Cross-Origin-Opener-Policy Cross-Origin-Embedder-Policy",
                encoding="utf-8",
            )
            (root / "README.md").write_text("Supply your own ROM. No game data is included.", encoding="utf-8")
            results = mod.audit(root)
            stats = mod.summary(results)
            self.assertEqual(stats["critical_miss"], 0)
            self.assertGreaterEqual(stats["pass"], 9)

    def test_empty_tree_fails_strict_requirements(self):
        with tempfile.TemporaryDirectory() as td:
            results = mod.audit(Path(td))
            stats = mod.summary(results)
            self.assertGreater(stats["critical_miss"], 0)

    def test_build_directories_are_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build-wasm").mkdir()
            (root / "build-wasm" / "generated.js").write_text(
                "EMSCRIPTEN -pthread WebGL2 Cross-Origin-Opener-Policy",
                encoding="utf-8",
            )
            stats = mod.summary(mod.audit(root))
            self.assertGreater(stats["critical_miss"], 0)


if __name__ == "__main__":
    unittest.main()
