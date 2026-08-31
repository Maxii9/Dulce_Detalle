from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_venta_tipo_movimiento_alter_venta_metodo_pago'),
    ]

    operations = [
        migrations.AddField(
            model_name='negocio',
            name='envio_domicilio',
            field=models.BooleanField(default=True, verbose_name='Envío a domicilio'),
        ),
        migrations.AddField(
            model_name='negocio',
            name='envio_retiro',
            field=models.BooleanField(default=True, verbose_name='Retiro en tienda'),
        ),
        migrations.AddField(
            model_name='negocio',
            name='envio_convenir',
            field=models.BooleanField(default=True, verbose_name='A convenir'),
        ),
    ]
