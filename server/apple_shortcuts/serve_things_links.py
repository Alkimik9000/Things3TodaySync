#!/usr/bin/env python3
"""Serve generated Things3 URLs over HTTP.

Expose ``/next`` which returns the next unserved URL from
``generated_things_urls.txt``. The last served index is stored in
``last_served_url.txt``.
"""

from __future__ import annotations

import http.server
import os
import socketserver
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent
URLS_FILE = BASE_DIR / "generated_things_urls.txt"
STATE_FILE = BASE_DIR / "last_served_url.txt"


def load_urls() -> List[str]:
    if not URLS_FILE.exists():
        return []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def read_index() -> int:
    if not STATE_FILE.exists():
        return 0
    try:
        return int(STATE_FILE.read_text().strip())
    except ValueError:
        return 0


def write_index(idx: int) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(idx))


class LinkHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/next":
            urls = load_urls()
            idx = read_index()
            if idx < len(urls):
                url = urls[idx]
                write_index(idx + 1)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(url.encode("utf-8"))
            else:
                self.send_response(204)
                self.end_headers()
            return
        super().do_GET()


def run(port: int = 8000) -> None:
    with socketserver.TCPServer(("", port), LinkHandler) as httpd:
        print(f"Serving links on port {port} at /next")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run(port)
