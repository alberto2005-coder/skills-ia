"""Cobros de juguete para el fixture del plan y de los objetivos de mutación."""


def charge(amount, balance):
    """Descuenta el importe del saldo si hay fondos suficientes."""
    if amount <= 0:
        raise ValueError("importe inválido")
    if amount > balance:
        return None
    return balance - amount
