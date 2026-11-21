"""Misma API con las cuatro familias cerradas.

Inerte: no se ejecuta ni se importa. Sirve de contraste para no marcar como
hallazgo lo que ya está mitigado.
"""

from urllib.parse import urlparse

from flask import Flask, request

app = Flask(__name__)

ALLOWED_FIELDS = {"nombre", "email"}
SAFE_HOSTS = {"api.example.com"}
PEDIDOS = {}


def require_role(role):
    """Guarda de función: la identidad no basta."""
    raise NotImplementedError


@app.get("/pedidos/<pedido_id>")
def leer_pedido(pedido_id):
    tenant = request.headers.get("X-Tenant")
    return PEDIDOS.get((tenant, pedido_id), {})


@app.post("/admin/usuarios")
@require_role("admin")
def crear_usuario_admin():
    campos = {key: value for key, value in request.json.items() if key in ALLOWED_FIELDS}
    return {"ok": True, "payload": campos}


@app.put("/usuarios/<usuario_id>")
def actualizar_usuario(usuario_id):
    campos = {key: value for key, value in request.json.items() if key in ALLOWED_FIELDS}
    return {"id": usuario_id, **campos}


@app.post("/fetch")
def traer_url():
    host = urlparse(request.json["url"]).hostname
    if host not in SAFE_HOSTS:
        return {"error": "host no permitido"}, 400
    import requests

    return requests.get("https://%s" % host, timeout=5).text
