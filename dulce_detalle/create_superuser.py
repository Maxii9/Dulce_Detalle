import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dulce_detalle.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

user, created = User.objects.get_or_create(username='maxi')
if created or not user.is_superuser:
    user.set_password('river43436508')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print("Superusuario maxi creado/actualizado correctamente.")
else:
    # If exists, update password and flags just in case
    user.set_password('river43436508')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print("Superusuario maxi actualizado.")
