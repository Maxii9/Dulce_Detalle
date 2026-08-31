# -*- coding: utf-8 -*-
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

"""
Script de carga masiva de productos desde una carpeta publica de Google Drive.

ESTRATEGIA: descarga y procesa UNA SUBCARPETA A LA VEZ.
- Si Drive bloquea una subcarpeta, espera 5 minutos y reintenta solo esa.
- Las subcarpetas ya procesadas no se vuelven a tocar.
- Los productos ya creados se saltan automaticamente.

USO:
  ..\\env\\Scripts\\python.exe cargar_desde_drive.py <link_de_drive>

Las subcarpetas de Drive que corresponden a la estructura conocida:
  Página web/
  +-- (imagenes sueltas)
  +-- Maquillaje/
      +-- Aromad/
      +-- Bazar/
      +-- Bases, cor, polvo y rubor/
      +-- ... etc
"""

import re
import io
import time
import shutil
import tempfile
import django
from pathlib import Path

try:
    import gdown
except ImportError:
    print("[ERROR] Instala gdown: pip install gdown")
    sys.exit(1)

try:
    from PIL import Image
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# ── Django setup ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dulce_detalle.settings")
django.setup()

from django.core.files.base import ContentFile                    # noqa: E402
from app.models import Negocio, CategoriaProducto, Producto      # noqa: E402

# ── Config ────────────────────────────────────────────────────────────────────
EXTENSIONES_IMAGEN  = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
TIENDA_DEFAULT      = "mango-accesorio"
NOMBRE_DEFAULT      = "Falta"
CATEGORIA_DEFAULT   = "Falta"
PRECIO_DEFAULT      = 1
COSTO_DEFAULT       = 0
STOCK_DEFAULT       = 1
MAX_NOMBRE_ARCHIVO  = 90
MAX_BYTES_IMAGEN    = 8 * 1024 * 1024   # 8 MB
MAX_REINTENTOS      = 8
ESPERA_BLOQUEO      = 5 * 60            # 5 minutos

# IDs de subcarpetas conocidas (se completan al listar la raiz)
# Formato: {"nombre": "id"}
SUBCARPETAS_MAQUILLAJE = {
    "Aromad":                      "1YLepMuO-L-J8ue44pbr5PMNjStgQbJI5",
    "Balamo":                      "1INO3-nqNzpC1tS6PEQh0o3pTHkKFPDfE",
    "Bases, cor, polvo y rubor":   "1t6ZSvZ1eA8Qdq5vJY_OarDJJRUu9RqhO",
    "Bazar":                       "1tU7xmrZELINfMJkdVFpumx6OEWtXpDVe",
    "Cabello":                     "1bHjwzT3FmFfGqHpWpNP9oFm3pN5Zl5zM",
    "Gloss":                       "1hZt_IVX0D9lF0A3bJZWkPipfLi3nHl_a",
    "Herramientas de belleza":     "1_xYKc9U2qNqT9MN3NZkxlC0pX8v0Eewf",
    "Labiales":                    "1dGKxmhQ3PKH0aWOy9nF3yqH5BHBZ9ZMO",
    "Libreria y papeleria":        "1fVMhXV5JqkZyJ6VE3MxCpJmF_gHBV0Dp",
    "Marcarilla":                  "1vWnN6z2nmHqxDUh9uV3dXb9lKDa2QdXN",
    "Medias ninos":                "1Ru3mEh7HA5q3p_MFzFZlBr5KJxLm7DQu",
    "Ojos y delineadores":         "1xNt3v7XZKjRx-Jl5VoKlBgc9Zw3cBHQY",
    "Sombras":                     "18Jgz5T5MkJxYl0vPPq_FLrm0z5XiZGHJ",
}

_negocio_cache: dict = {}
_cat_cache: dict = {}


def get_negocio(slug):
    if slug not in _negocio_cache:
        try:
            _negocio_cache[slug] = Negocio.objects.get(slug=slug)
        except Negocio.DoesNotExist:
            _negocio_cache[slug] = None
    return _negocio_cache[slug]


def get_categoria(negocio, nombre):
    key = (negocio.pk, nombre)
    if key not in _cat_cache:
        cat, _ = CategoriaProducto.objects.get_or_create(negocio=negocio, nombre=nombre)
        _cat_cache[key] = cat
    return _cat_cache[key]


def extraer_folder_id(url):
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{25,}$", url.strip()):
        return url.strip()
    print(f"[ERROR] No se pudo extraer el folder ID de: {url}")
    sys.exit(1)


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
            print(f"   [COMPRIMIDA] {ruta.name[:50]} -> {len(datos)//1024}KB")
        except Exception as e:
            print(f"   [AVISO] No se pudo comprimir: {e}")
    return ContentFile(datos, name=nombre), nombre


def descargar_carpeta_con_reintentos(folder_id, tmp_dir, nombre_carpeta):
    """
    Descarga una carpeta de Drive a tmp_dir con reintentos automaticos.
    Devuelve True si tuvo exito (total o parcial), False si fallo completamente.
    """
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            gdown.download_folder(
                id=folder_id,
                output=str(tmp_dir),
                quiet=False,
                use_cookies=False,
            )
            return True
        except Exception as e:
            mensaje = str(e)
            es_bloqueo = any(k in mensaje for k in [
                "Cannot retrieve", "quota", "rate", "429", "403",
                "FileURLRetrievalError", "too many"
            ])
            if es_bloqueo and intento < MAX_REINTENTOS:
                print(f"\n[BLOQUEO] Drive bloqueo '{nombre_carpeta}' (intento {intento}/{MAX_REINTENTOS})")
                print(f"   Esperando 5 minutos...")
                for seg in range(ESPERA_BLOQUEO, 0, -30):
                    print(f"   Reintentando en {seg//60}:{seg%60:02d}...")
                    time.sleep(30)
                print(f"\n[REINTENTO {intento+1}] '{nombre_carpeta}'...\n")
                # Limpiar tmp antes de reintentar para evitar conflictos
                shutil.rmtree(tmp_dir, ignore_errors=True)
                tmp_dir.mkdir(parents=True, exist_ok=True)
            else:
                print(f"\n[ERROR] No se pudo descargar '{nombre_carpeta}': {e}")
                # Procesar lo que haya bajado parcialmente
                return False
    return False


def procesar_dir_local(carpeta, stats, nombre_carpeta):
    """Procesa imagenes de una carpeta local ya descargada."""
    imagenes = sorted(
        [f for f in carpeta.rglob("*")
         if f.is_file() and f.suffix.lower() in EXTENSIONES_IMAGEN],
        key=lambda f: f.name,
    )
    if not imagenes:
        print(f"   [AVISO] Sin imagenes en '{nombre_carpeta}'")
        return

    negocio = get_negocio(TIENDA_DEFAULT)
    if negocio is None:
        print(f"[ERROR] Tienda '{TIENDA_DEFAULT}' no existe.")
        stats["errores"] += len(imagenes)
        return

    categoria = get_categoria(negocio, CATEGORIA_DEFAULT)
    total = len(imagenes)
    print(f"\n[{nombre_carpeta}] {total} imagen(es) para subir")

    for idx, ruta in enumerate(imagenes, start=1):
        nombre_prod = NOMBRE_DEFAULT if total == 1 else f"{NOMBRE_DEFAULT} {idx:03d}"

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
            continue

        try:
            img_file, nombre_archivo = preparar_imagen(ruta)
            prod.imagen.save(nombre_archivo, img_file, save=True)
            print(f"  [+] ({idx:03d}/{total}) {nombre_prod}")
            stats["creados"] += 1
        except Exception as e:
            prod.delete()
            print(f"  [ERR] ({idx:03d}/{total}) '{ruta.name[:50]}': {e}")
            stats["errores"] += 1


def procesar_subcarpeta_drive(folder_id, nombre, stats):
    """Descarga UNA subcarpeta de Drive, la procesa y la elimina."""
    tmp = Path(tempfile.mkdtemp(prefix=f"drive_{nombre[:10]}_"))
    print(f"\n{'='*60}")
    print(f"[SUBCARPETA] {nombre}")
    print(f"{'='*60}")

    try:
        ok = descargar_carpeta_con_reintentos(folder_id, tmp, nombre)

        # Buscar la carpeta real dentro de tmp
        contenidos = [d for d in tmp.iterdir() if d.is_dir()]
        raiz = contenidos[0] if len(contenidos) == 1 else tmp

        procesar_dir_local(raiz, stats, nombre)

        if not ok:
            print(f"   [AVISO] Descarga parcial de '{nombre}' — algunos archivos pueden faltar.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def listar_subcarpetas_drive(folder_id):
    """
    Descarga SOLO la estructura (sin archivos) de una carpeta Drive
    para obtener los IDs de subcarpetas.
    Devuelve lista de (nombre, id).
    """
    tmp = Path(tempfile.mkdtemp(prefix="drive_list_"))
    subcarpetas = []
    try:
        # Descargar la carpeta en un dir temporal; luego leemos qué subdirs creó
        gdown.download_folder(
            id=folder_id,
            output=str(tmp),
            quiet=True,
            use_cookies=False,
        )
        # gdown crea la estructura de carpetas aunque los archivos fallen
        raiz = tmp
        contenidos = [d for d in tmp.iterdir() if d.is_dir()]
        if len(contenidos) == 1:
            raiz = contenidos[0]

        for sub in sorted(raiz.iterdir()):
            if sub.is_dir():
                subcarpetas.append(sub.name)
    except Exception:
        pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return subcarpetas


def main():
    if len(sys.argv) < 2:
        print("[ERROR] Pasa el link de la carpeta Drive.")
        print('   Ejemplo: ..\\env\\Scripts\\python.exe cargar_desde_drive.py "https://drive.google.com/drive/folders/1ABC..."')
        sys.exit(1)

    link      = sys.argv[1]
    folder_id = extraer_folder_id(link)

    negocio = get_negocio(TIENDA_DEFAULT)
    if negocio is None:
        disponibles = list(Negocio.objects.values_list("nombre", "slug"))
        print(f"[ERROR] Tienda '{TIENDA_DEFAULT}' no existe. Disponibles: {disponibles}")
        sys.exit(1)

    print(f"\n[INICIO] Drive ID  : {folder_id}")
    print(f"         Tienda    : {negocio.nombre}")
    print(f"         Categoria : {CATEGORIA_DEFAULT}")
    print(f"         Nombre    : {NOMBRE_DEFAULT}\n")

    stats = {"creados": 0, "existentes": 0, "errores": 0}

    # IDs conocidos de la exploracion previa de la carpeta
    # Estructura:  Pagina web (raiz) -> Maquillaje -> subcarpetas
    MAQUILLAJE_ID = "1inl0ABi7-_B2519KRyu88i_7UrBzlx1H"

    # Subcarpetas de Maquillaje con sus IDs reales (obtenidos del browser)
    SUBCARPETAS = [
        ("Aromad",                    "1YLepMuO-L-J8ue44pbr5PMNjStgQbJI5"),
        ("Balamo",                    "1INO3-nqNzpC1tS6PEQh0o3pTHkKFPDfE"),
        ("Bases, cor, polvo y rubor", "1t6ZSvZ1eA8Qdq5vJY_OarDJJRUu9RqhO"),
        ("Bazar",                     "1tU7xmrZELINfMJkdVFpumx6OEWtXpDVe"),
        ("Cabello",                   "1bHjwzT3FmFfGqHpWpNP9oFm3pN5Zl5zM"),
        ("Gloss",                     "1hZt_IVX0D9lF0A3bJZWkPipfLi3nHl_a"),
        ("Herramientas de belleza",   "1_xYKc9U2qNqT9MN3NZkxlC0pX8v0Eewf"),
        ("Labiales",                  "1dGKxmhQ3PKH0aWOy9nF3yqH5BHBZ9ZMO"),
        ("Libreria y papeleria",      "1fVMhXV5JqkZyJ6VE3MxCpJmF_gHBV0Dp"),
        ("Marcarilla",                "1vWnN6z2nmHqxDUh9uV3dXb9lKDa2QdXN"),
        ("Medias ninos",              "1Ru3mEh7HA5q3p_MFzFZlBr5KJxLm7DQu"),
        ("Ojos y delineadores",       "1xNt3v7XZKjRx-Jl5VoKlBgc9Zw3cBHQY"),
        ("Sombras",                   "18Jgz5T5MkJxYl0vPPq_FLrm0z5XiZGHJ"),
    ]

    # ── Paso 1: imagenes sueltas de la raiz ──────────────────────────────────
    # La raiz tiene muchas imagenes sueltas (las que vimos en el browser)
    # Las descargamos como una carpeta completa
    print("[PASO 1] Descargando imagenes sueltas de la carpeta raiz...")
    procesar_subcarpeta_drive(folder_id, "Pagina web", stats)

    # ── Paso 2: cada subcarpeta de Maquillaje por separado ───────────────────
    total_subs = len(SUBCARPETAS)
    for i, (nombre, sub_id) in enumerate(SUBCARPETAS, 1):
        if not sub_id:
            print(f"\n[SKIP] {nombre} — ID desconocido, omitida")
            continue
        print(f"\n[{i}/{total_subs}] Procesando subcarpeta: {nombre}")
        procesar_subcarpeta_drive(sub_id, nombre, stats)

    print()
    print("=" * 60)
    print(f"[OK]    Creados:     {stats['creados']}")
    print(f"[SKIP]  Ya existian: {stats['existentes']}")
    print(f"[ERR]   Errores:     {stats['errores']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
