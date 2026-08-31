from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_negocio_velocidad_carrusel_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='negocio',
            name='estilo_fuente',
            field=models.CharField(
                choices=[
                    ('abril',     'Abril Fatface — Itálica bold'),
                    ('playfair',  'Playfair Display — Elegante serif'),
                    ('bebas',     'Bebas Neue — Mayúsculas compactas'),
                    ('dancing',   'Dancing Script — Cursíva manuscrita'),
                    ('righteous', 'Righteous — Redondeada moderna'),
                    ('unbounded', 'Unbounded — Geométrica sin serif'),
                ],
                default='abril',
                max_length=15,
                verbose_name='Estilo de fuente del título',
            ),
        ),
    ]
