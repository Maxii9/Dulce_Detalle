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

    @property
    def pedidos_pendientes_count(self):
        return self.pedidos.filter(estado='pendiente').count()

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

class Insumo(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='insumos')
    nombre = models.CharField(max_length=150)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} (${self.costo_unitario})"

    class Meta:
        ordering = ['nombre']

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='pedidos')
    cliente_nombre = models.CharField(max_length=150)
    cliente_telefono = models.CharField(max_length=50)
    cliente_direccion = models.CharField(max_length=250, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente_nombre} - ${self.total}"

    class Meta:
        ordering = ['-creado']

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_pedido')
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
