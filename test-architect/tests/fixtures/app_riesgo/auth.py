"""Autenticación de juguete para el fixture del plan de pruebas."""

TOKENS = {}


def login(user, password):
    """Devuelve un token si las credenciales no vienen vacías."""
    if not user or not password:
        return None
    token = "t-" + user
    TOKENS[token] = user
    return token


def verify(token):
    """Usuario asociado al token, o None si no existe."""
    return TOKENS.get(token)
