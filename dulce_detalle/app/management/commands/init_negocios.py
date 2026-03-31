from django.core.management.base import BaseCommand
from app.models import Negocio


class Command(BaseCommand):
    help = 'Inicializa los dos negocios base en la base de datos'

    def handle(self, *args, **options):
        negocios_data = [
            {
                'slug': 'bijouteria',
                'nombre': 'Mango Accesorios',
                'descripcion': 'Accesorios, joyas y artículos de moda para toda ocasión.',
                'color_primario': '#7c3aed',
                'color_secundario': '#6d28d9',
                'emoji': '👜',
            },
            {
                'slug': 'dulceria',
                'nombre': 'Dulce Detalle',
                'descripcion': 'Dulces, golosinas y delicias para endulzar tu día.',
                'color_primario': '#db2777',
                'color_secundario': '#be185d',
                'emoji': '🍬',
            },
        ]

        for data in negocios_data:
            negocio, created = Negocio.objects.get_or_create(
                slug=data['slug'],
                defaults=data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Negocio creado: {negocio.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {negocio.nombre}'))

        self.stdout.write(self.style.SUCCESS('\n✨ Negocios inicializados correctamente.'))
