#!/usr/bin/env python3
"""Serve a browser/Wasm build with headers required by SharedArrayBuffer."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class IsolatedHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8932)
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    handler = lambda *a, **kw: IsolatedHandler(*a, directory=str(directory), **kw)  # noqa: E731
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {directory} at http://{args.host}:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
