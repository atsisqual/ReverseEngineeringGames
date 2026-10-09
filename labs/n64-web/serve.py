#!/usr/bin/env python3
"""Serve a Wasm build with isolation headers needed by serious threaded ports."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="build/n64-web")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(args.dir).resolve()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(root)))
    print(f"Serving {root} at http://127.0.0.1:{args.port}/reg_n64_web_smoke.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
