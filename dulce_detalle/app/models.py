from django.db import models


class Negocio(models.Model):
    TIPOS = [
        ('bijouteria', 'Bijoutería'),
        ('dulceria', 'Dulcería'),
    ]
    slug = models.CharField(max_length=20, unique=True, choices=TIPOS)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    color_primario = models.CharField(max_length=7, default='#6d28d9')
    color_secundario = models.CharField(max_length=7, default='#7c3aed')
    emoji = models.CharField(max_length=5, default='🛍️')

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.negocio.nombre})"

    class Meta:
        ordering = ['-creado']
