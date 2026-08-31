"""
Script de carga de 20 productos demo para la tienda "admin".

Uso (BD de Render - producción):
  python cargar_productos.py <DATABASE_URL> <SECRET_KEY>

  Ejemplo:
  python cargar_productos.py "postgresql://user:pass@host/db" "mi-secret-key"

También podés setear las variables de entorno antes de correr:
  $env:DATABASE_URL  = "postgresql://..."
  $env:SECRET_KEY    = "..."
  python cargar_productos.py
"""

import os
import sys

# ── Recibir DATABASE_URL y SECRET_KEY por argumento o variable de entorno ─────
if len(sys.argv) >= 2:
    os.environ["DATABASE_URL"] = sys.argv[1]
if len(sys.argv) >= 3:
    os.environ["SECRET_KEY"] = sys.argv[2]

# Si no hay SECRET_KEY seteada, usar una de desarrollo genérica
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "django-insecure-script-carga-dev-only-no-usar-en-prod"

if not os.environ.get("DATABASE_URL"):
    print("❌ Necesitás pasar la DATABASE_URL de Render como primer argumento.")
    print('   Ejemplo: python cargar_productos.py "postgresql://user:pass@host/db"')
    sys.exit(1)

import django  # noqa: E402

# ── Configuración Django ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dulce_detalle.settings")
django.setup()

from app.models import Negocio, CategoriaProducto, Producto  # noqa: E402

# ── Buscar la tienda del superuser/admin ──────────────────────────────────────
try:
    negocio = Negocio.objects.get(slug="admin")
except Negocio.DoesNotExist:
    # Si no existe con slug "admin", tomar la primera disponible
    negocio = Negocio.objects.first()
    if not negocio:
        print("[ERROR] No se encontro ningun Negocio. Crea uno desde el panel admin primero.")
        sys.exit(1)
    print(f"[AVISO] No se encontro tienda con slug 'admin'. Usando: {negocio.nombre}")

print(f"[OK] Tienda objetivo: {negocio.nombre} (slug: {negocio.slug})")

# ── Crear (o recuperar) categorías ──────────────────────────────────────────
CATEGORIAS = ["Medias & Calcetines", "Maquillaje", "Accesorios", "Cuidado Personal", "Bijouterie"]

cats = {}
for nombre_cat in CATEGORIAS:
    cat, created = CategoriaProducto.objects.get_or_create(negocio=negocio, nombre=nombre_cat)
    cats[nombre_cat] = cat
    estado = "creada" if created else "ya existia"
    print(f"  [CAT] '{nombre_cat}' — {estado}")

# ── Datos de los 20 productos ─────────────────────────────────────────────────
PRODUCTOS = [
    # ── Medias & Calcetines ──────────────────────────────────────────────────
    {
        "nombre": "Medias Tobilleras Algodón x3",
        "categoria": "Medias & Calcetines",
        "precio": 2500,
        "costo": 1200,
        "stock": 50,
        "descripcion": "Pack de 3 pares de medias tobilleras de algodón peinado. Ideal para el uso diario, muy cómodas y duraderas. Talle único.",
        "codigo_barras": "7790001000001",
    },
    {
        "nombre": "Medias Deportivas Antideslizantes",
        "categoria": "Medias & Calcetines",
        "precio": 1800,
        "costo": 900,
        "stock": 35,
        "descripcion": "Medias deportivas con suela antideslizante, perfectas para yoga, pilates y uso en interiores. Talón reforzado.",
        "codigo_barras": "7790001000002",
    },
    {
        "nombre": "Medias de Compresión Viaje",
        "categoria": "Medias & Calcetines",
        "precio": 3200,
        "costo": 1600,
        "stock": 20,
        "descripcion": "Medias de compresión graduada ideal para viajes largos y largas jornadas de pie. Previene el cansancio y la hinchazón.",
        "codigo_barras": "7790001000003",
    },
    {
        "nombre": "Medias Fantasía Lunares x2",
        "categoria": "Medias & Calcetines",
        "precio": 1500,
        "costo": 700,
        "stock": 45,
        "descripcion": "Pack de 2 pares de medias con estampado de lunares coloridos. Talla única. Ideal para regalar o usar con estilo.",
        "codigo_barras": "7790001000004",
    },
    {
        "nombre": "Medias Térmicas Invierno",
        "categoria": "Medias & Calcetines",
        "precio": 2800,
        "costo": 1400,
        "stock": 30,
        "descripcion": "Medias térmicas de lana merino para el frío extremo. Súper abrigadas, sin picazón. Ideales para montaña o inviernos rigurosos.",
        "codigo_barras": "7790001000005",
    },

    # ── Maquillaje ───────────────────────────────────────────────────────────
    {
        "nombre": "Base de Maquillaje Líquida FPS 30",
        "categoria": "Maquillaje",
        "precio": 5500,
        "costo": 2800,
        "stock": 25,
        "descripcion": "Base líquida de cobertura media-alta con factor de protección solar 30. Fórmula liviana, acaba mate. Disponible en 6 tonos.",
        "codigo_barras": "7790002000001",
    },
    {
        "nombre": "Máscara de Pestañas Volumen Extremo",
        "categoria": "Maquillaje",
        "precio": 3800,
        "costo": 1900,
        "stock": 40,
        "descripcion": "Máscara de pestañas con fórmula enriquecida con aceite de ricino. Da volumen, longitud y curvatura sin apelmazar.",
        "codigo_barras": "7790002000002",
    },
    {
        "nombre": "Paleta de Sombras 12 Colores Nude",
        "categoria": "Maquillaje",
        "precio": 6200,
        "costo": 3100,
        "stock": 18,
        "descripcion": "Paleta de sombras de ojos en tonos nude y marrones ahumados. Alta pigmentación, acabados mate y shimmer. Ideal para el día y la noche.",
        "codigo_barras": "7790002000003",
    },
    {
        "nombre": "Labial Líquido Mate Larga Duración",
        "categoria": "Maquillaje",
        "precio": 2900,
        "costo": 1450,
        "stock": 55,
        "descripcion": "Labial líquido con fórmula mate de larga duración (hasta 12 h). No transfiere, no reseca los labios. Disponible en 8 tonos.",
        "codigo_barras": "7790002000004",
    },
    {
        "nombre": "Corrector Iluminador Ojeras",
        "categoria": "Maquillaje",
        "precio": 3400,
        "costo": 1700,
        "stock": 30,
        "descripcion": "Corrector líquido con partículas iluminadoras para disimular ojeras y aportar luminosidad al rostro. Fórmula hidratante.",
        "codigo_barras": "7790002000005",
    },

    # ── Accesorios ───────────────────────────────────────────────────────────
    {
        "nombre": "Broche Mariposa Pasador x6",
        "categoria": "Accesorios",
        "precio": 1200,
        "costo": 500,
        "stock": 80,
        "descripcion": "Set de 6 broches mariposa metálicos plateados y dorados para el cabello. Fijación fuerte, no dañan el pelo.",
        "codigo_barras": "7790003000001",
    },
    {
        "nombre": "Vincha Acetato Flores",
        "categoria": "Accesorios",
        "precio": 1800,
        "costo": 900,
        "stock": 60,
        "descripcion": "Vincha de acetato con motivo floral en relieve. Diseño elegante y moderno, perfecta para looks formales e informales.",
        "codigo_barras": "7790003000002",
    },
    {
        "nombre": "Liga de Tela Satinada x5",
        "categoria": "Accesorios",
        "precio": 900,
        "costo": 400,
        "stock": 100,
        "descripcion": "Pack de 5 ligas de tela satinada en colores pasteles. Suaves con el cabello, sin marca ni romperlo.",
        "codigo_barras": "7790003000003",
    },
    {
        "nombre": "Hebilla Clip French Dorada x4",
        "categoria": "Accesorios",
        "precio": 1600,
        "costo": 750,
        "stock": 70,
        "descripcion": "Set de 4 hebillas clip estilo francés en tono dorado viejo. Ideales para medios peinados y peinados elegantes.",
        "codigo_barras": "7790003000004",
    },
    {
        "nombre": "Pañuelo de Seda Estampado",
        "categoria": "Accesorios",
        "precio": 4500,
        "costo": 2200,
        "stock": 25,
        "descripcion": "Pañuelo de seda con estampado geométrico. Versátil: úsalo en el cabello, el cuello o la cartera. 60x60 cm.",
        "codigo_barras": "7790003000005",
    },

    # ── Cuidado Personal ─────────────────────────────────────────────────────
    {
        "nombre": "Mascarilla Facial Arcilla Rosa",
        "categoria": "Cuidado Personal",
        "precio": 3500,
        "costo": 1750,
        "stock": 35,
        "descripcion": "Mascarilla de arcilla rosa con extracto de rosas silvestres. Limpia profundamente los poros, aporta luminosidad y suavidad.",
        "codigo_barras": "7790004000001",
    },
    {
        "nombre": "Sérum Vitamina C Hidratante 30 ml",
        "categoria": "Cuidado Personal",
        "precio": 7200,
        "costo": 3600,
        "stock": 20,
        "descripcion": "Sérum concentrado de vitamina C al 15%. Unifica el tono de piel, reduce manchas y aporta luminosidad. Apto para todo tipo de piel.",
        "codigo_barras": "7790004000002",
    },
    {
        "nombre": "Crema Hidratante Manos Rosa Mosqueta",
        "categoria": "Cuidado Personal",
        "precio": 2200,
        "costo": 1100,
        "stock": 45,
        "descripcion": "Crema hidratante para manos con aceite de rosa mosqueta y vitamina E. Absorción rápida, no grasosa. 75 ml.",
        "codigo_barras": "7790004000003",
    },

    # ── Bijouterie ───────────────────────────────────────────────────────────
    {
        "nombre": "Aros Argolla Dorada Pequeña",
        "categoria": "Bijouterie",
        "precio": 1500,
        "costo": 650,
        "stock": 90,
        "descripcion": "Aros argolla pequeña en baño de oro 18k. Livianos y resistentes, perfectos para el uso diario. Diámetro 2 cm.",
        "codigo_barras": "7790005000001",
    },
    {
        "nombre": "Collar Cristal Corazón Plateado",
        "categoria": "Bijouterie",
        "precio": 2800,
        "costo": 1200,
        "stock": 40,
        "descripcion": "Collar fino con dije de corazón de cristal y cadena plateada. Cierre tipo mosquetón, largo ajustable 40-45 cm.",
        "codigo_barras": "7790005000002",
    },
]

# ── Insertar productos ─────────────────────────────────────────────────────────
creados = 0
existentes = 0

for data in PRODUCTOS:
    cat = cats[data["categoria"]]
    prod, created = Producto.objects.get_or_create(
        negocio=negocio,
        nombre=data["nombre"],
        defaults={
            "categoria": cat,
            "precio": data["precio"],
            "costo": data["costo"],
            "stock": data["stock"],
            "descripcion": data["descripcion"],
            "codigo_barras": data.get("codigo_barras"),
        },
    )
    if created:
        creados += 1
        print(f"  [+] Creado: {prod.nombre} -- ${prod.precio}")
    else:
        existentes += 1
        print(f"  [=] Ya existia: {prod.nombre}")

print()
print(f"[FIN] Proceso finalizado. Creados: {creados} | Ya existian: {existentes}")
print(f"      Total de productos en la tienda: {negocio.productos.count()}")
