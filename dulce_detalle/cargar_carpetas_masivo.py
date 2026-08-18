# -*- coding: utf-8 -*-
# Carga masiva desde multiples carpetas locales con indice global unico.

import os, sys, io
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dulce_detalle.settings")
django.setup()

from django.core.files.base import ContentFile         # noqa: E402
from app.models import Negocio, CategoriaProducto, Producto  # noqa: E402

try:
    from PIL import Image
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False
    print("[AVISO] Pillow no instalado. Imagenes >8MB pueden fallar.")

# ── Configuración ──────────────────────────────────────────────────────────────
TIENDA_SLUG        = "mango-accesorio"
NOMBRE_DEFAULT     = "Falta"
CATEGORIA_DEFAULT  = "Falta"
PRECIO_DEFAULT     = 1
COSTO_DEFAULT      = 0
STOCK_DEFAULT      = 1
CARPETAS_OMITIR    = {"Simpsons", "simpsons"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
MAX_BYTES_IMAGEN   = 8 * 1024 * 1024
MAX_NOMBRE_ARCHIVO = 90


def nombre_archivo_seguro(nombre):
    sufijo   = Path(nombre).suffix
    base     = Path(nombre).stem
    max_base = MAX_NOMBRE_ARCHIVO - len(sufijo)
    return base[:max_base] + sufijo


def preparar_imagen(ruta):
    datos  = ruta.read_bytes()
    nombre = nombre_archivo_seguro(ruta.name)
    if len(datos) > MAX_BYTES_IMAGEN and PILLOW_OK:
        try:
            img = Image.open(io.BytesIO(datos))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            calidad = 85
            while calidad >= 40:
                buf.seek(0); buf.truncate()
                img.save(buf, format="JPEG", quality=calidad, optimize=True)
                if buf.tell() <= MAX_BYTES_IMAGEN:
                    break
                calidad -= 10
            datos  = buf.getvalue()
            nombre = nombre_archivo_seguro(ruta.stem[:MAX_NOMBRE_ARCHIVO - 4] + ".jpg")
            print(f"     [COMPRIMIDA] {ruta.name[:50]} -> {len(datos)//1024}KB")
        except Exception as e:
            print(f"     [AVISO] No se pudo comprimir {ruta.name[:50]}: {e}")
    elif len(datos) > MAX_BYTES_IMAGEN and not PILLOW_OK:
        raise ValueError(f"Imagen demasiado grande ({len(datos)//1024//1024}MB). Instala Pillow.")
    return ContentFile(datos, name=nombre), nombre


def main():
    if len(sys.argv) < 2:
        print("USO: ..\env\Scripts\python.exe cargar_carpetas_masivo.py <ruta_base>")
        sys.exit(1)

    ruta_base = Path(sys.argv[1]).resolve()
    if not ruta_base.is_dir():
        print(f"[ERROR] No existe: {ruta_base}")
        sys.exit(1)

    # ── Negocio y categoría ────────────────────────────────────────────────────
    try:
        negocio = Negocio.objects.get(slug=TIENDA_SLUG)
    except Negocio.DoesNotExist:
        print(f"[ERROR] Tienda '{TIENDA_SLUG}' no existe.")
        sys.exit(1)

    categoria, _ = CategoriaProducto.objects.get_or_create(
        negocio=negocio, nombre=CATEGORIA_DEFAULT
    )

    print(f"\n[INICIO] Tienda   : {negocio.nombre}")
    print(f"         Categoria: {categoria.nombre}")
    print(f"         Carpeta  : {ruta_base}\n")

    # ── Obtener índice de partida (siguiente número disponible) ────────────────
    ultimo = (
        Producto.objects
        .filter(negocio=negocio, nombre__startswith=NOMBRE_DEFAULT)
        .count()
    )
    indice_global = ultimo + 1
    print(f"[INFO] Productos '{NOMBRE_DEFAULT}' existentes: {ultimo} → siguiente índice: {indice_global:03d}\n")

    # ── Carpetas a procesar ────────────────────────────────────────────────────
    carpetas = sorted(
        [d for d in ruta_base.iterdir()
         if d.is_dir() and d.name not in CARPETAS_OMITIR],
        key=lambda d: d.name.lower()
    )

    if not carpetas:
        print("[AVISO] No se encontraron subcarpetas.")
        sys.exit(0)

    stats = {"creados": 0, "existentes": 0, "errores": 0}

    for carpeta in carpetas:
        imagenes = sorted(
            [f for f in carpeta.iterdir()
             if f.is_file() and f.suffix.lower() in EXTENSIONES_IMAGEN],
            key=lambda f: f.name
        )
        if not imagenes:
            print(f"[SKIP] {carpeta.name} — sin imagenes")
            continue

        print(f"\n{'='*60}")
        print(f"[CARPETA] {carpeta.name}  ({len(imagenes)} imagenes)")
        print(f"{'='*60}")

        for ruta in imagenes:
            nombre_prod = f"{NOMBRE_DEFAULT} {indice_global:03d}"

            prod, created = Producto.objects.get_or_create(
                negocio=negocio,
                nombre=nombre_prod,
                defaults={
                    "categoria":   categoria,
                    "precio":      PRECIO_DEFAULT,
                    "costo":       COSTO_DEFAULT,
                    "stock":       STOCK_DEFAULT,
                    "descripcion": "",
                },
            )

            if not created:
                print(f"  [=] Ya existe: {nombre_prod}")
                stats["existentes"] += 1
                indice_global += 1
                continue

            try:
                img_file, nombre_archivo = preparar_imagen(ruta)
                prod.imagen.save(nombre_archivo, img_file, save=True)
                print(f"  [+] {nombre_prod}  ←  {ruta.name[:50]}")
                stats["creados"] += 1
            except Exception as e:
                prod.delete()
                print(f"  [ERR] {nombre_prod}: {e}")
                stats["errores"] += 1

            indice_global += 1

    print(f"\n{'='*60}")
    print(f"[OK]    Creados:     {stats['creados']}")
    print(f"[SKIP]  Ya existian: {stats['existentes']}")
    print(f"[ERR]   Errores:     {stats['errores']}")
    total = Producto.objects.filter(negocio=negocio).count()
    print(f"        Total en tienda: {total}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
