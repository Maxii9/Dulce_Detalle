import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dulce_detalle.settings')
django.setup()

from django.contrib.auth import get_user_model
from app.models import Negocio, Producto, CategoriaProducto

User = get_user_model()

def run_migration():
    # 1. Crear el usuario administrador
    user, created = User.objects.get_or_create(
        username='Pablo Solis',
        defaults={'email': 'pablosolisok@gmail.com'}
    )
    if created or not user.check_password('1313'):
        user.set_password('1313')
        user.save()

    print("Usuario Pablo Solis consolidado.")

    # 2. Asignar todos los Negocios huérfanos a Pablo
    Negocio.objects.filter(propietario__isnull=True).update(propietario=user)
    print("Negocios asignados al propietario.")

    # 3. Mapeo de Categorías
    TIPOS_DICT = dict(Producto.TIPO_CHOICES)
    
    for negocio in Negocio.objects.all():
        # Crear las categorías base si no existieran (asumiendo que es su primera vez o ya tenían productos)
        for t_slug, t_name in TIPOS_DICT.items():
            CategoriaProducto.objects.get_or_create(negocio=negocio, nombre=t_name)
    
        # Revisar los productos. Tenían "tipo" en minúscula/slug, los pasamos a nombre legible.
        productos = Producto.objects.filter(negocio=negocio)
        for p in productos:
            if p.tipo in TIPOS_DICT:
                p.tipo = TIPOS_DICT[p.tipo] # e.g. "papeleria" -> "Papelería"
                p.save()
    
    print("Tipos de productos migrados a CategoriaProducto.")

if __name__ == '__main__':
    run_migration()
