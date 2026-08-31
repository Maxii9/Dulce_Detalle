#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

# Limpia la BD si FLUSH_DB=true (solo usar una vez, luego quitar la variable)
if [ "$FLUSH_DB" = "true" ]; then
  echo "⚠️  FLUSH_DB=true — Borrando todos los datos..."
  python manage.py flush --no-input
  echo "✅ Base de datos limpiada."
fi

python manage.py migrate

# Crea el superusuario SOLO si no existe todavía.
# NUNCA sobreescribe la contraseña de un usuario existente.
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py shell <<EOF
from django.contrib.auth.models import User
import os
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" creado correctamente.')
else:
    print(f'Superuser "{username}" ya existe — no se modifica la contraseña.')
EOF
fi
