import ipaddress
import socket
from urllib.parse import urlparse

def is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False

def validate_target(url: str, allow_local: bool = False) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("URL no válida: utiliza http:// o https://")
    host = p.hostname.lower()
    if allow_local:
        if not is_loopback_host(host):
            raise ValueError("El modo local solo permite localhost/loopback.")
        return
    if host == "localhost":
        raise ValueError("Destino local bloqueado en modo web.")
    try:
        infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ValueError(f"No se pudo resolver el host: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            raise ValueError(f"Destino no público bloqueado: {ip}")
