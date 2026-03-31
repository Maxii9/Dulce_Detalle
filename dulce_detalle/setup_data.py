"""
Script de inicio: crea las tablas y carga los negocios iniciales.
Ejecutar con: env\Scripts\python setup_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dulce_detalle.settings')
django.setup()

from django.core.management import call_command
from app.models import Negocio

# 1. Correr migraciones
print("→ Corriendo migraciones...")
call_command('migrate', verbosity=1)

# 2. Crear negocios si no existen
datos = [
    {
        'slug': 'bijouteria',
        'nombre': 'Mango Accesorios',
        'descripcion': 'Tienda de bijoutería y accesorios',
        'color_primario': '#b45309',
        'color_secundario': '#d97706',
        'emoji': '✨',
    },
    {
        'slug': 'dulceria',
        'nombre': 'Dulce Detalle',
        'descripcion': 'Tienda de dulces y detalles',
        'color_primario': '#be185d',
        'color_secundario': '#db2777',
        'emoji': '🍬',
    },
]

print("\n→ Creando negocios...")
for d in datos:
    negocio, creado = Negocio.objects.get_or_create(slug=d['slug'], defaults=d)
    estado = "creado ✅" if creado else "ya existía ⚠️"
    print(f"  {negocio.emoji} {negocio.nombre} ({negocio.slug}) — {estado}")

print("\n¡Todo listo! Podés iniciar el servidor con:")
print("  env\\Scripts\\python manage.py runserver")
