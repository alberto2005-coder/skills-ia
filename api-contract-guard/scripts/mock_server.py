"""Levanta un servidor HTTP local que responde según un contrato OpenAPI.

Uso:
    py api-contract-guard/scripts/mock_server.py --spec api.json --port 8080

Solo escucha en `127.0.0.1`, sin red externa. Para tests se importa `serve()`,
que devuelve el servidor y el puerto efímero asignado.

Código de salida: 0 al cerrar con Ctrl+C · 2 contrato ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def match_path(spec: dict, path: str) -> str | None:
    """Ruta declarada que corresponde a `path`, con `{param}` como comodín."""
    paths = spec.get("paths", {})
    if path in paths:
        return path
    for template in paths:
        if "{" not in template:
            continue
        pattern = "^" + re.sub(r"\{[^/]+\}", "[^/]+", re.escape(template).replace(r"\{", "{").replace(r"\}", "}")) + "$"
        if re.match(pattern, path):
            return template
    return None


def example_for(spec: dict, method: str, path: str) -> dict:
    operation = spec.get("paths", {}).get(path, {}).get(method.lower(), {})
    responses = operation.get("responses", {})
    for code in ("200", "201", 200, 201):
        response = responses.get(code) or responses.get(str(code))
        if not response:
            continue
        for media in response.get("content", {}).values():
            if "example" in media:
                return media["example"]
            schema = media.get("schema", {})
            if "example" in schema:
                return schema["example"]
    return {"mock": path, "method": method.upper()}


def build_handler(spec: dict) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _reply(self, method: str) -> None:
            path = self.path.split("?", 1)[0].rstrip("/") or "/"
            # Coincidencia exacta o por plantilla (`/items/{id}`): antes solo
            # valían rutas literales y cualquier parámetro daba 404.
            declared = match_path(spec, path)
            operations = spec.get("paths", {}).get(declared) if declared else None
            if not operations or method.lower() not in operations:
                self.send_error(404, "ruta no declarada en el contrato")
                return
            payload = json.dumps(example_for(spec, method, declared), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802 (nombre que exige BaseHTTPRequestHandler)
            self._reply("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._reply("POST")

        def do_PUT(self) -> None:  # noqa: N802
            self._reply("PUT")

        def do_PATCH(self) -> None:  # noqa: N802
            self._reply("PATCH")

        def do_DELETE(self) -> None:  # noqa: N802
            self._reply("DELETE")

        def do_HEAD(self) -> None:  # noqa: N802
            self._reply("HEAD")

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._reply("OPTIONS")

        def log_message(self, *args) -> None:
            return

    return Handler


def serve(spec: dict, port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread, int]:
    server = ThreadingHTTPServer(("127.0.0.1", port), build_handler(spec))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Servidor mock de un contrato OpenAPI.")
    parser.add_argument("--spec", required=True, help="contrato OpenAPI en JSON")
    parser.add_argument("--port", type=int, default=0, help="puerto local (0 elige uno libre)")
    args = parser.parse_args(argv)

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"contrato ilegible: {error}")
        return 2

    server, _, port = serve(spec, args.port)
    print(f"mock escuchando en http://127.0.0.1:{port}")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()
        print("mock detenido")
        return 0


if __name__ == "__main__":
    sys.exit(main())
