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
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    stock = models.IntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.negocio.nombre})"

    class Meta:
        ordering = ['-creado']


class Venta(models.Model):
    TIPO_CHOICES = [
        ('pagada', 'Pagada'),
        ('credito', 'A crédito'),
    ]
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia bancaria'),
        ('mercadopago', 'Mercado Pago'),
        ('qr', 'QR'),
        ('otro', 'Otro'),
    ]
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='ventas')
    fecha = models.DateField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='pagada')
    metodo_pago = models.CharField(max_length=20, choices=METODO_CHOICES, default='efectivo')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacion = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta #{self.pk} — {self.negocio.nombre} — ${self.total}"

    @property
    def ganancia_total(self):
        return sum(item.ganancia for item in self.items.all())

    class Meta:
        ordering = ['-creado']


class ItemVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_venta')
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def ganancia(self):
        return self.cantidad * (self.precio_unitario - self.costo_unitario)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

class Nota(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='notas')
    texto = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"Nota de {self.negocio.nombre} - {self.creado.strftime('%d/%m/%Y')}"
