# -*- coding: utf-8 -*-
# Carga masiva de imágenes desde una carpeta PLANA (sin subcarpetas).
# Soporta reanudación: guarda progreso en un archivo .json junto a la carpeta.
# Maneja imágenes de muy alta resolución (>178MP) desactivando límite de Pillow.

import os, sys, io, json, time
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
from django.db import connection, OperationalError as DjangoOperationalError
from app.models import Negocio, CategoriaProducto, Producto  # noqa: E402

MAX_REINTENTOS_DB = 3
ESPERA_REINTENTO  = 5  # segundos entre reintentos de conexión

try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None  # Desactiva límite de "decompression bomb" para fotos de alta resolución
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False
    print("[AVISO] Pillow no instalado. Imágenes >8MB pueden fallar.")

# ── Configuración ──────────────────────────────────────────────────────────────
TIENDA_SLUG        = "mango-accesorio"
NOMBRE_DEFAULT     = "Falta"
CATEGORIA_DEFAULT  = "Falta"
PRECIO_DEFAULT     = 1
COSTO_DEFAULT      = 0
STOCK_DEFAULT      = 1
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
MAX_BYTES_IMAGEN   = 9 * 1024 * 1024   # 9MB — por debajo del límite de 10MB de Cloudinary
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


def cargar_checkpoint(ruta_checkpoint):
    if ruta_checkpoint.exists():
        try:
            with open(ruta_checkpoint, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[RESUME] Checkpoint encontrado: {len(data['procesadas'])} imágenes ya procesadas.")
            return data
        except Exception as e:
            print(f"[AVISO] No se pudo leer checkpoint: {e}. Empezando desde cero.")
    return {"procesadas": [], "errores": []}


def guardar_checkpoint(ruta_checkpoint, data):
    with open(ruta_checkpoint, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reconectar_db():
    """Cierra la conexión caída para que Django abra una nueva en el próximo query."""
    try:
        connection.close()
    except Exception:
        pass


def main():
    if len(sys.argv) < 2:
        print("USO: ..\\env\\Scripts\\python.exe cargar_imagenes_directo.py <ruta_carpeta>")
        print("     Agrega --reset para ignorar el checkpoint y empezar de cero.")
        sys.exit(1)

    ruta_carpeta = Path(sys.argv[1]).resolve()
    reset_mode   = "--reset" in sys.argv

    if not ruta_carpeta.is_dir():
        print(f"[ERROR] No existe: {ruta_carpeta}")
        sys.exit(1)

    # Archivo de progreso junto a la carpeta de imágenes
    ruta_checkpoint = ruta_carpeta / "_progreso_carga.json"

    # ── Negocio y categoría ────────────────────────────────────────────────────
    try:
        negocio = Negocio.objects.get(slug=TIENDA_SLUG)
    except Negocio.DoesNotExist:
        print(f"[ERROR] Tienda '{TIENDA_SLUG}' no existe.")
        sys.exit(1)

    categoria, creada = CategoriaProducto.objects.get_or_create(
        negocio=negocio, nombre=CATEGORIA_DEFAULT
    )
    if creada:
        print(f"[INFO] Categoría '{CATEGORIA_DEFAULT}' creada nueva.")

    # ── Imágenes en la raíz de la carpeta ─────────────────────────────────────
    imagenes = sorted(
        [f for f in ruta_carpeta.iterdir()
         if f.is_file() and f.suffix.lower() in EXTENSIONES_IMAGEN],
        key=lambda f: f.name
    )

    if not imagenes:
        print("[AVISO] No se encontraron imágenes en la carpeta.")
        sys.exit(0)

    # ── Checkpoint ────────────────────────────────────────────────────────────
    if reset_mode and ruta_checkpoint.exists():
        ruta_checkpoint.unlink()
        print("[RESET] Checkpoint eliminado. Empezando de cero.")

    checkpoint = cargar_checkpoint(ruta_checkpoint)
    ya_procesadas = set(checkpoint["procesadas"])

    imagenes_pendientes = [f for f in imagenes if f.name not in ya_procesadas]

    print(f"\n[INICIO] Tienda   : {negocio.nombre}")
    print(f"         Categoría: {categoria.nombre}")
    print(f"         Carpeta  : {ruta_carpeta}")
    print(f"         Total    : {len(imagenes)} imágenes")
    print(f"         Ya listas: {len(ya_procesadas)}")
    print(f"         Pendientes: {len(imagenes_pendientes)}\n")

    if not imagenes_pendientes:
        print("[OK] Todas las imágenes ya fueron procesadas. ¡Listo!")
        sys.exit(0)

    # ── Índice de partida ──────────────────────────────────────────────────────
    ultimo = (
        Producto.objects
        .filter(negocio=negocio, nombre__startswith=NOMBRE_DEFAULT)
        .count()
    )
    indice_global = ultimo + 1
    print(f"[INFO] Productos '{NOMBRE_DEFAULT}' en DB: {ultimo} → siguiente índice: {indice_global:03d}\n")
    print(f"{'='*60}")

    stats = {"creados": 0, "existentes": 0, "errores": 0}

    for ruta in imagenes_pendientes:
        nombre_prod = f"{NOMBRE_DEFAULT} {indice_global:03d}"

        # ── get_or_create con retry de conexión ───────────────────────────────
        prod = None
        created = False
        for intento in range(1, MAX_REINTENTOS_DB + 1):
            try:
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
                break  # éxito
            except Exception as db_err:
                print(f"  [DB-ERR intento {intento}/{MAX_REINTENTOS_DB}] {nombre_prod}: {db_err}")
                reconectar_db()
                if intento == MAX_REINTENTOS_DB:
                    print(f"  [FATAL] No se pudo conectar a la DB. Abortando.")
                    # Guardar estado antes de salir
                    guardar_checkpoint(ruta_checkpoint, checkpoint)
                    sys.exit(1)
                time.sleep(ESPERA_REINTENTO)

        if not created:
            print(f"  [=] Ya existe: {nombre_prod} — saltando")
            stats["existentes"] += 1
            checkpoint["procesadas"].append(ruta.name)
            guardar_checkpoint(ruta_checkpoint, checkpoint)
            indice_global += 1
            continue

        try:
            img_file, nombre_archivo = preparar_imagen(ruta)
            prod.imagen.save(nombre_archivo, img_file, save=True)
            print(f"  [+] {nombre_prod}  ←  {ruta.name[:60]}")
            stats["creados"] += 1
            # ✅ Guardar progreso después de cada éxito
            checkpoint["procesadas"].append(ruta.name)
            guardar_checkpoint(ruta_checkpoint, checkpoint)
        except Exception as e:
            prod.delete()
            print(f"  [ERR] {nombre_prod}: {e}")
            stats["errores"] += 1
            checkpoint["errores"].append({"archivo": ruta.name, "error": str(e)})
            guardar_checkpoint(ruta_checkpoint, checkpoint)

        indice_global += 1

    print(f"\n{'='*60}")
    print(f"[OK]    Creados:     {stats['creados']}")
    print(f"[SKIP]  Ya existían: {stats['existentes']}")
    print(f"[ERR]   Errores:     {stats['errores']}")
    total = Producto.objects.filter(negocio=negocio).count()
    print(f"        Total en tienda: {total}")
    print(f"{'='*60}")

    if stats["errores"] == 0 and ruta_checkpoint.exists():
        ruta_checkpoint.unlink()
        print("[LIMPIEZA] Checkpoint eliminado (proceso completo sin errores).")


if __name__ == "__main__":
    main()
