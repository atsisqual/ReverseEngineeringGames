from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_files_exist():
    required = [
        ROOT / "CMakeLists.txt",
        ROOT / "include/reg/n64_web_host.hpp",
        ROOT / "src/n64_web_host.cpp",
        ROOT / "src/smoke_main.cpp",
        ROOT / "serve.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"missing: {missing}"


def test_no_game_material_extensions():
    forbidden = {".z64", ".n64", ".v64", ".rom", ".iso"}
    hits = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in forbidden]
    assert not hits
