from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SurfaceLabTests(unittest.TestCase):
    def test_canvas_and_emdawn_port_are_wired(self):
        cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
        cpp = (ROOT / "main.cpp").read_text(encoding="utf-8")
        shell = (ROOT / "shell.html").read_text(encoding="utf-8")

        self.assertIn("--use-port=emdawnwebgpu", cmake)
        self.assertIn("EmscriptenSurfaceSourceCanvasHTMLSelector", cpp)
        self.assertIn('selector = "#canvas"', cpp)
        self.assertIn('id="canvas"', shell)

    def test_server_enables_cross_origin_isolation(self):
        server = (ROOT / "serve.py").read_text(encoding="utf-8")
        self.assertIn('Cross-Origin-Opener-Policy", "same-origin', server)
        self.assertIn('Cross-Origin-Embedder-Policy", "require-corp', server)
        self.assertIn('Cross-Origin-Resource-Policy", "same-origin', server)


if __name__ == "__main__":
    unittest.main()
