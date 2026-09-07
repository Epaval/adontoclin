#!/usr/bin/env python3
"""
Generador de claves de licencia - SOLO VENDEDOR
Nunca compartas este archivo ni el SECRET.

Uso:
  python3 tools/generar_licencia.py HUELLA anual
  python3 tools/generar_licencia.py HUELLA anual --hasta 2027-12-31
  python3 tools/generar_licencia.py HUELLA perpetua
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.core.licencias import generar_clave


def main():
    parser = argparse.ArgumentParser(description="Genera claves de licencia")
    parser.add_argument("huella", help="Codigo de maquina del cliente")
    parser.add_argument("tipo", choices=["anual", "perpetua"], nargs="?", default="perpetua")
    parser.add_argument("--hasta", help="Fecha de vencimiento AAAA-MM-DD (solo anual)")
    args = parser.parse_args()

    hasta = None
    if args.hasta:
        hasta = datetime.strptime(args.hasta, "%Y-%m-%d")

    clave = generar_clave(args.huella, args.tipo, hasta=hasta)

    print("=" * 50)
    print(f"Huella:  {args.huella.upper()}")
    print(f"Tipo:    {args.tipo}")
    if args.tipo == "anual":
        vence = hasta or None
        print(f"Vence:   {(vence and vence.strftime('%d/%m/%Y')) or 'hoy + 365 dias'}")
    print(f"CLAVE:   {clave}")
    print("=" * 50)


if __name__ == "__main__":
    main()
