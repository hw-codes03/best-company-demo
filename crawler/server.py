"""Serves the generated site/ folder on a local web server for the crawler to fetch from."""

import contextlib
import functools
import http.server
import threading

from .settings import SITE_DIR


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the terminal tidy
        pass


@contextlib.contextmanager
def serve_site():
    """Start a server on a free local port, yield its base URL, then shut it down."""
    handler = functools.partial(_QuietHandler, directory=str(SITE_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
