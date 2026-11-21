"""API de ejemplo con las cuatro familias del API Security Top 10.

Inerte: no se ejecuta ni se importa. Cada ruta lleva su regla en un comentario
para que el test pueda cruzarla con `references/api-security-top10.md`.
"""

from flask import Flask, request

app = Flask(__name__)

PEDIDOS = {}


@app.get("/pedidos/<pedido_id>")
def leer_pedido(pedido_id):
    # regla: bola-sin-scope — el id de la ruta no se filtra por propietario
    return PEDIDOS[pedido_id]


@app.post("/admin/usuarios")
def crear_usuario_admin():
    # regla: bfla-sin-rol — autenticación sin comprobación de rol
    return {"ok": True, "payload": request.json}


@app.put("/usuarios/<usuario_id>")
def actualizar_usuario(usuario_id):
    # regla: mass-assignment — el cuerpo entero se vuelca en el modelo
    campos = request.json
    return {"id": usuario_id, **campos}


@app.post("/fetch")
def traer_url():
    # regla: ssrf-sin-allowlist — URL del usuario directa al cliente HTTP
    import requests

    return requests.get(request.json["url"], timeout=5).text
