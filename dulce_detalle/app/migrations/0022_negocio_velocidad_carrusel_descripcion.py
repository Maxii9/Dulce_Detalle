from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_producto_codigo_barras'),
    ]

    operations = [
        migrations.AddField(
            model_name='negocio',
            name='velocidad_carrusel',
            field=models.CharField(
                choices=[('lento', 'Lento (90s)'), ('normal', 'Normal (60s)'), ('rapido', 'Rápido (35s)')],
                default='normal',
                max_length=10,
                verbose_name='Velocidad del carrusel',
            ),
        ),
        migrations.AddField(
            model_name='negocio',
            name='mostrar_descripcion',
            field=models.BooleanField(
                default=False,
                help_text='Si está activado, se muestra el texto de descripción debajo del nombre de la tienda.',
                verbose_name='Mostrar descripción en la tienda pública',
            ),
        ),
    ]
