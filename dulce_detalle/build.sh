#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create or update superuser
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py shell <<EOF
from django.contrib.auth.models import User
import os
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
user, created = User.objects.get_or_create(username=username)
user.email = email
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.save()
print(f'Superuser {"created" if created else "updated"} successfully.')
EOF
fi
