# -*- coding: utf-8 -*-
"""Tests del camino HTTP con un servidor local (sin red externa).

Cubren los fallos que la suite offline no podía ver:
  - el cuerpo gzip/deflate se descomprime antes de parsear;
  - `audit --mode page|local` informa del modo real, no siempre «source»;
  - `rescore` dice la puntuación anterior, no la ruta del fichero.
"""
import contextlib
import gzip
import io
import json
import sys
import tempfile
import threading
import unittest
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import cli, perf, security, web_audit
from scripts.httpbody import decode_body
from scripts.page import parse_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"

HTML = (
    b"<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
    b"<title>Servidor de prueba</title>"
    b"<meta name=\"description\" content=\"Descripcion de prueba con longitud "
    b"suficiente para no disparar el aviso de metadatos ausentes.\">"
    b"</head><body><h1>Pagina servida en local</h1>"
    b"<p>Contenido visible con palabras suficientes para calcular el ratio de "
    b"texto sobre HTML sin que el analisis lo marque como muestra pequena.</p>"
    b"</body></html>"
)


class _Handler(BaseHTTPRequestHandler):
    hits = 0  # peticiones servidas a /plain (para probar que no hay 2º salto)

    def log_message(self, *args):  # silencio: el test no ensucia la salida
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/redirect"):
            target = {
                "/redirect-ok": "/plain",
                "/redirect-private": "http://10.255.255.1/plain",
                "/redirect-loopback": "http://127.0.0.1:%d/plain"
                                     % self.server.server_address[1],
            }.get(path)
            if target:
                self.send_response(302)
                self.send_header("Location", target)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        if path == "/robots.txt":
            body, ctype, encoding = b"User-agent: *\nAllow: /\n", "text/plain", None
        elif path in ("/llms.txt", "/llms-full.txt", "/sitemap.xml"):
            self.send_error(404)
            return
        elif path == "/gzip":
            body, ctype, encoding = gzip.compress(HTML), "text/html; charset=utf-8", "gzip"
        elif path == "/deflate":
            body, ctype, encoding = zlib.compress(HTML), "text/html; charset=utf-8", "deflate"
        else:
            body, ctype, encoding = HTML, "text/html; charset=utf-8", None
            if path == "/plain":
                type(self).hits += 1

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        if encoding:
            self.send_header("Content-Encoding", encoding)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class HttpTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)


class DecompressionTests(HttpTestCase):
    def test_decode_body_handles_gzip_and_deflate(self):
        self.assertEqual(decode_body(gzip.compress(HTML), {"content-encoding": "gzip"}), HTML)
        self.assertEqual(decode_body(zlib.compress(HTML), {"content-encoding": "deflate"}), HTML)
        self.assertEqual(decode_body(HTML, {}), HTML)

    def test_measure_returns_readable_html(self):
        measured = perf.measure(self.base + "/gzip", allow_local=True)
        self.assertTrue(measured["body"].startswith(b"<!doctype html>"))
        self.assertEqual(measured["headers"].get("content-encoding"), "gzip")
        self.assertEqual(parse_html(measured["body"].decode("utf-8")).title,
                         "Servidor de prueba")

    def test_crawl_parses_gzipped_page(self):
        result = web_audit.audit_web(self.base + "/gzip", max_pages=2,
                                     allow_local=True, rate=50)
        self.assertEqual(result["data"]["page"]["title"], "Servidor de prueba")
        self.assertGreaterEqual(result["pages_scanned"], 1)
        self.assertIn("Servidor de prueba", result["data"]["page"]["title"])
        # El peso medido es el del HTML descomprimido, no el del bloque gzip.
        self.assertGreaterEqual(result["data"]["perf"]["html_bytes"], len(HTML))

    def test_crawl_parses_deflated_page(self):
        result = web_audit.audit_web(self.base + "/deflate", max_pages=2,
                                     allow_local=True, rate=50)
        self.assertEqual(result["data"]["page"]["title"], "Servidor de prueba")


class ModeReportingTests(HttpTestCase):
    def _payload(self, *args):
        with tempfile.TemporaryDirectory() as tmp:
            cli.main(list(args) + ["--output", tmp])
            audit = next(Path(tmp).glob("**/audit.json"))
            return json.loads(audit.read_text(encoding="utf-8"))

    def test_mode_local(self):
        payload = self._payload("audit", self.base + "/plain", "--mode", "local",
                                "--rate", "50", "--max-pages", "2")
        self.assertEqual(payload["mode"], "local")

    def test_mode_page(self):
        payload = self._payload("audit", str(FIXTURES / "page_full.html"),
                                "--mode", "page")
        self.assertEqual(payload["mode"], "page")

    def test_module_command_on_file_reports_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli.main(["onpage", str(FIXTURES / "page_full.html"), "--output", tmp])
            payload = json.loads((Path(tmp) / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "page")


class RedirectTests(HttpTestCase):
    """SSRF por redirección: se valida cada salto, no solo la URL inicial."""

    def setUp(self):
        _Handler.hits = 0

    def test_web_mode_blocks_redirect_to_loopback(self):
        opener = security.build_safe_opener(allow_local=False)
        with self.assertRaises(ValueError):
            opener.open(self.base + "/redirect-loopback", timeout=10)
        self.assertEqual(_Handler.hits, 0, "se siguió el salto bloqueado")

    def test_local_mode_blocks_redirect_to_private_ip(self):
        with self.assertRaises(ValueError):
            web_audit.fetch(self.base + "/redirect-private", allow_local=True)
        self.assertEqual(_Handler.hits, 0, "se siguió el salto a 10.255.255.1")

    def test_allowed_redirect_is_followed(self):
        data = web_audit.fetch(self.base + "/redirect-ok", allow_local=True)
        self.assertEqual(data["status"], 200)
        self.assertIn(b"Servidor de prueba", data["body"])
        self.assertEqual(_Handler.hits, 1)

    def test_http_ok_blocks_private_redirect(self):
        self.assertFalse(cli._http_ok(self.base + "/redirect-private",
                                      allow_local=True))
        self.assertEqual(_Handler.hits, 0)

    def test_http_ok_follows_allowed_redirect(self):
        self.assertTrue(cli._http_ok(self.base + "/redirect-ok", allow_local=True))
        self.assertEqual(_Handler.hits, 1)

    def test_measure_follows_allowed_redirect(self):
        measured = perf.measure(self.base + "/redirect-ok", allow_local=True)
        self.assertEqual(measured["status"], 200)
        self.assertEqual(parse_html(measured["body"].decode("utf-8")).title,
                         "Servidor de prueba")


class RescoreMessageTests(unittest.TestCase):
    def test_message_shows_previous_score_not_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli.main(["audit", str(FIXTURES / "page_full.html"),
                      "--mode", "page", "--output", tmp])
            audit = next(Path(tmp).glob("**/audit.json"))
            before = json.loads(audit.read_text(encoding="utf-8"))["score"]

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                cli.main(["rescore", str(audit), "--output", str(Path(tmp) / "r")])
            line = next(entry for entry in buffer.getvalue().splitlines() if "antes" in entry)

            self.assertIn("%.1f/100" % before, line)
            self.assertNotIn("audit.json", line)


if __name__ == "__main__":
    unittest.main()
