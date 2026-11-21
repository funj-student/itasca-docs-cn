"""Serve the repository under the GitHub Pages subpath /itasca-docs-cn/.

Usage: python3 tests/pages_server.py [root] [port]
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
PREFIX = '/itasca-docs-cn/'


class PagesHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = unquote(path.split('?', 1)[0].split('#', 1)[0])
        if path.startswith(PREFIX):
            path = '/' + path[len(PREFIX):]
        elif path == '/itasca-docs-cn':
            path = '/'
        return super().translate_path(path)

    def log_message(self, fmt, *args):
        pass


os.chdir(ROOT)
ThreadingHTTPServer(('127.0.0.1', PORT), PagesHandler).serve_forever()
