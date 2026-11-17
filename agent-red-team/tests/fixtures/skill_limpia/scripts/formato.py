#!/usr/bin/env python3
"""Comprobador de longitud de líneas. Solo lectura, sin red ni subprocess."""

import argparse
from pathlib import Path

MAX_POR_DEFECTO = 80


def lineas_largas(texto, maximo):
    """Devuelve (numero_de_linea, longitud) de cada línea que supera el máximo."""
    resultado = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if len(linea) > maximo:
            resultado.append((numero, len(linea)))
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Lista las líneas que superan el máximo.")
    parser.add_argument("fichero", help="Ruta del fichero de texto a revisar")
    parser.add_argument("--max", type=int, default=MAX_POR_DEFECTO, help="Longitud máxima permitida")
    args = parser.parse_args()

    texto = Path(args.fichero).read_text(encoding="utf-8")
    for numero, longitud in lineas_largas(texto, args.max):
        print(f"Línea {numero}: {longitud} caracteres")


if __name__ == "__main__":
    main()
