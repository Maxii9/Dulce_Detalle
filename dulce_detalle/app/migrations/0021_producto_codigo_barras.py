from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_imagenproducto'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='codigo_barras',
            field=models.CharField(
                blank=True, db_index=True, max_length=50,
                null=True, unique=True,
                verbose_name='Código de barras'
            ),
        ),
    ]
