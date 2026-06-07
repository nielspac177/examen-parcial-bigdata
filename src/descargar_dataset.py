# -*- coding: utf-8 -*-
"""Descarga el dataset NetCDF del examen (no se versiona por su tamano, ~71 MB).

Uso (desde la raiz del repo):
    python src/descargar_dataset.py
"""
import os
import urllib.request

URL = ("https://github.com/encinasquille/DataLifecyclePy/raw/main/"
       "data/raw/ARM_sgpmetE32.b1.2021.nc")
DEST = os.path.join("data", "ARM_sgpmetE32.b1.2021.nc")


def main():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DEST):
        print(f"Ya existe: {DEST} ({os.path.getsize(DEST)/1e6:.1f} MB)")
        return
    print(f"Descargando desde {URL} ...")
    urllib.request.urlretrieve(URL, DEST)
    print(f"Guardado en {DEST} ({os.path.getsize(DEST)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
