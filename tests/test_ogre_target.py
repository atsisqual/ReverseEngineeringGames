import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "targets" / "ogre-battle-64" / "prepare.py"
spec = importlib.util.spec_from_file_location("ogre_prepare", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OgreTargetTests(unittest.TestCase):
    def test_manifest_is_pinned(self):
        manifest = json.loads((MODULE_PATH.parent / "target.json").read_text())
        self.assertRegex(manifest["upstream"]["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(manifest["runtime"]["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(manifest["runtime"]["n64recomp_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(manifest["input"]["expected_size_bytes"], 40 * 1024 * 1024)

    def test_rom_validation_checks_magic_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            rom = Path(td) / "game.z64"
            with rom.open("wb") as fh:
                fh.write(mod.N64_MAGIC)
                fh.truncate(mod.TARGET["input"]["expected_size_bytes"])
            mod.validate_rom(rom)

    def test_wrong_magic_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            rom = Path(td) / "game.z64"
            with rom.open("wb") as fh:
                fh.write(b"BAD!")
                fh.truncate(mod.TARGET["input"]["expected_size_bytes"])
            with self.assertRaises(SystemExit):
                mod.validate_rom(rom)


if __name__ == "__main__":
    unittest.main()
