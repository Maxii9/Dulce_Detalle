"""
Script de carga masiva de productos con imágenes desde una carpeta.

ESTRUCTURA ESPERADA DE LA CARPETA:
────────────────────────────────────
mi_carpeta/
├── info.txt          ← datos del producto (obligatorio)
├── imagen1.jpg
├── imagen2.png
├── imagen3.webp
└── ...

FORMATO DEL info.txt:
────────────────────────────────────
nombre=Medias Soquetes Los Simpsons
categoria=Medias soquetes adultos
precio=2000
costo=900
stock=0
descripcion=Medias de algodón, talle único adulto.
tienda=mango-accesorio

CLAVES:
  nombre      → (obligatorio) Nombre base del producto. Si hay más de 1 imagen,
                se agrega un número: "Nombre 001", "Nombre 002", etc.
  categoria   → (obligatorio) Nombre exacto de la categoría (se crea si no existe).
  precio      → (obligatorio) Precio de venta en pesos.
  costo       → (obligatorio) Costo de compra en pesos.
  tienda      → (obligatorio) Slug del negocio destino (ej: mango-accesorio).
  stock       → (opcional, default=0)
  descripcion → (opcional, default="")

USO:
  ..\\env\\Scripts\\python.exe cargar_desde_carpeta.py <ruta_a_la_carpeta>

  Ejemplo:
  ..\env\Scripts\python.exe cargar_desde_carpeta.py "C:\\fotos\\simpsons"
"""

import os
import sys
import django
from pathlib import Path

# ── Configuración de Django ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dulce_detalle.settings")
django.setup()

from django.core.files import File  # noqa: E402
from app.models import Negocio, CategoriaProducto, Producto  # noqa: E402


# ── Extensiones de imagen aceptadas ──────────────────────────────────────────
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}


def leer_info(carpeta: Path) -> dict:
    """Lee y parsea el archivo info.txt dentro de la carpeta."""
    ruta_info = carpeta / "info.txt"
    if not ruta_info.exists():
        print("[ERROR] No se encontro 'info.txt' en la carpeta.")
        print(f"   Ruta buscada: {ruta_info}")
        sys.exit(1)

    datos = {}
    with open(ruta_info, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            datos[clave.strip().lower()] = valor.strip()

    # Validar campos obligatorios
    requeridos = ["nombre", "categoria", "precio", "costo", "tienda"]
    for campo in requeridos:
        if campo not in datos:
            print(f"[ERROR] Falta el campo obligatorio '{campo}' en info.txt")
            sys.exit(1)

    return datos


def obtener_imagenes(carpeta: Path) -> list[Path]:
    """Devuelve lista de archivos de imagen en la carpeta, ordenados."""
    imagenes = sorted(
        [f for f in carpeta.iterdir()
         if f.is_file() and f.suffix.lower() in EXTENSIONES_IMAGEN]
    )
    if not imagenes:
        print("[AVISO] No se encontraron imagenes en la carpeta.")
        print(f"   Extensiones aceptadas: {', '.join(sorted(EXTENSIONES_IMAGEN))}")
        sys.exit(1)
    return imagenes


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Debes indicar la ruta de la carpeta como argumento.")
        print("   Ejemplo: python cargar_desde_carpeta.py \"C:\\fotos\\simpsons\"")
        sys.exit(1)

    carpeta = Path(sys.argv[1]).resolve()
    if not carpeta.is_dir():
        print(f"[ERROR] La ruta no existe o no es una carpeta: {carpeta}")
        sys.exit(1)

    print(f"\n[CARPETA] {carpeta}\n")

    # ── Leer info.txt ────────────────────────────────────────────────────────
    datos = leer_info(carpeta)

    nombre_base    = datos["nombre"]
    nombre_cat     = datos["categoria"]
    precio         = float(datos["precio"])
    costo          = float(datos["costo"])
    tienda_slug    = datos["tienda"]
    stock          = int(datos.get("stock", "0"))
    descripcion    = datos.get("descripcion", "")

    # ── Buscar negocio ────────────────────────────────────────────────────────
    try:
        negocio = Negocio.objects.get(slug=tienda_slug)
    except Negocio.DoesNotExist:
        print(f"[ERROR] No existe ninguna tienda con el slug '{tienda_slug}'.")
        negocios_disponibles = Negocio.objects.values_list("nombre", "slug")
        print("   Tiendas disponibles:")
        for n, s in negocios_disponibles:
            print(f"     - {n}  (slug: {s})")
        sys.exit(1)

    print(f"[TIENDA] {negocio.nombre} (slug: {negocio.slug})")

    # ── Buscar / crear categoría ─────────────────────────────────────────────
    categoria, creada_cat = CategoriaProducto.objects.get_or_create(
        negocio=negocio, nombre=nombre_cat
    )
    estado_cat = "creada" if creada_cat else "ya existia"
    print(f"[CATEGORIA] {categoria.nombre} ({estado_cat})")

    # ── Obtener imágenes ─────────────────────────────────────────────────────
    imagenes = obtener_imagenes(carpeta)
    total = len(imagenes)
    print(f"[IMAGENES] Encontradas: {total}\n")

    creados    = 0
    existentes = 0
    errores    = 0

    for idx, ruta_imagen in enumerate(imagenes, start=1):
        # Nombre del producto: "Nombre Base 001", "Nombre Base 002"...
        if total == 1:
            nombre_prod = nombre_base
        else:
            nombre_prod = f"{nombre_base} {idx:03d}"

        # ── Crear o recuperar el producto ────────────────────────────────────
        prod, created = Producto.objects.get_or_create(
            negocio=negocio,
            nombre=nombre_prod,
            defaults={
                "categoria": categoria,
                "precio":    precio,
                "costo":     costo,
                "stock":     stock,
                "descripcion": descripcion,
            },
        )

        if not created:
            existentes += 1
            print(f"  [=] ({idx:03d}/{total}) Ya existia: {nombre_prod}")
            continue

        # ── Subir imagen al producto ─────────────────────────────────────────
        try:
            with open(ruta_imagen, "rb") as img_file:
                prod.imagen.save(ruta_imagen.name, File(img_file), save=True)
            creados += 1
            print(f"  [+] ({idx:03d}/{total}) Creado con imagen: {nombre_prod}")
        except Exception as e:
            errores += 1
            prod.delete()   # revertir si falla la subida de imagen
            print(f"  [ERROR] ({idx:03d}/{total}) Fallo imagen para '{nombre_prod}': {e}")

    # ── Resumen ───────────────────────────────────────────────────────────────
    print()
    print("-" * 50)
    print(f"[OK]     Creados:        {creados}")
    print(f"[SKIP]   Ya existian:    {existentes}")
    print(f"[ERROR]  Errores:        {errores}")
    print(f"         Total imagenes: {total}")
    print(f"         Total productos en tienda: {negocio.productos.count()}")
    print("-" * 50)


if __name__ == "__main__":
    main()
