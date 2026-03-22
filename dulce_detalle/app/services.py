"""
Capa de servicios para la lógica CRUD de Productos, Negocios y Ventas.
Las vistas delegan toda la lógica de datos a este módulo.
"""
from decimal import Decimal
from .models import Negocio, Producto, Venta, ItemVenta


# ── Negocios ──────────────────────────────────────────────────────────────

def get_negocios():
    """Retorna todos los negocios disponibles."""
    return Negocio.objects.all()


def get_negocio(slug: str) -> Negocio | None:
    """Retorna un negocio por su slug, o None si no existe."""
    try:
        return Negocio.objects.get(slug=slug)
    except Negocio.DoesNotExist:
        return None


def get_negocio_activo(session) -> Negocio | None:
    """Lee el slug guardado en la sesión y retorna el negocio correspondiente."""
    slug = session.get('negocio_slug')
    if not slug:
        return Negocio.objects.first()
    return get_negocio(slug)


# ── Productos ─────────────────────────────────────────────────────────────

def get_productos(negocio_slug: str):
    """Lista todos los productos de un negocio dado su slug."""
    return Producto.objects.filter(negocio__slug=negocio_slug).select_related('negocio')


def get_producto(pk: int) -> Producto | None:
    """Retorna un producto por su PK, o None si no existe."""
    try:
        return Producto.objects.select_related('negocio').get(pk=pk)
    except Producto.DoesNotExist:
        return None


def crear_producto(negocio: Negocio, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None) -> Producto:
    """Crea y retorna un nuevo producto para el negocio dado."""
    return Producto.objects.create(
        negocio=negocio,
        nombre=nombre,
        precio=precio,
        costo=costo,
        descripcion=descripcion,
        stock=stock,
        imagen=imagen,
    )


def actualizar_producto(pk: int, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None) -> Producto | None:
    """Actualiza un producto existente. Retorna el producto actualizado o None."""
    producto = get_producto(pk)
    if producto is None:
        return None
    producto.nombre = nombre
    producto.precio = precio
    producto.costo = costo
    producto.descripcion = descripcion
    producto.stock = stock
    if imagen:
        producto.imagen = imagen
    producto.save()
    return producto


def eliminar_producto(pk: int) -> bool:
    """Elimina un producto por PK. Retorna True si fue eliminado, False si no existía."""
    producto = get_producto(pk)
    if producto is None:
        return False
    producto.delete()
    return True


# ── Carrito (session-based) ───────────────────────────────────────────────

def get_carrito(session: dict) -> dict:
    """Retorna el carrito actual de la sesión como dict {pk_str: cantidad}."""
    return session.get('carrito', {})


def carrito_agregar(session: dict, producto_pk: int) -> None:
    """Agrega 1 unidad del producto al carrito de la sesión."""
    carrito = session.get('carrito', {})
    key = str(producto_pk)
    carrito[key] = carrito.get(key, 0) + 1
    session['carrito'] = carrito
    session.modified = True


def carrito_quitar(session: dict, producto_pk: int) -> None:
    """Quita el producto del carrito (sin importar la cantidad)."""
    carrito = session.get('carrito', {})
    carrito.pop(str(producto_pk), None)
    session['carrito'] = carrito
    session.modified = True


def carrito_limpiar(session: dict) -> None:
    """Vacía el carrito completo."""
    session['carrito'] = {}
    session.modified = True


def get_carrito_detalle(session: dict) -> list[dict]:
    """
    Retorna lista de dicts con info del carrito:
    [{producto, cantidad, subtotal}, ...]
    """
    carrito = get_carrito(session)
    items = []
    for pk_str, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(pk=int(pk_str))
            subtotal = Decimal(str(producto.precio)) * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        except Producto.DoesNotExist:
            pass
    return items


def carrito_total(session: dict) -> Decimal:
    """Calcula el total del carrito."""
    return sum(item['subtotal'] for item in get_carrito_detalle(session)) or Decimal('0')


# ── Ventas ────────────────────────────────────────────────────────────────

def get_ventas(negocio_slug: str):
    """Lista todas las ventas de un negocio."""
    return Venta.objects.filter(negocio__slug=negocio_slug).prefetch_related('items__producto')


def crear_venta(negocio: Negocio, fecha, tipo: str, metodo_pago: str, items_data: list) -> Venta:
    """
    Crea una venta con sus items.
    items_data: lista de dicts {producto, cantidad}
    """
    total = sum(Decimal(str(item['producto'].precio)) * item['cantidad'] for item in items_data)
    venta = Venta.objects.create(
        negocio=negocio,
        fecha=fecha,
        tipo=tipo,
        metodo_pago=metodo_pago,
        total=total,
    )
    for item in items_data:
        ItemVenta.objects.create(
            venta=venta,
            producto=item['producto'],
            cantidad=item['cantidad'],
            precio_unitario=item['producto'].precio,
            costo_unitario=item['producto'].costo,
        )
    return venta


def get_resumen_estadisticas(negocio_slug: str) -> dict:
    from django.utils import timezone
    hoy = timezone.now().date()
    # Lunes de esta semana
    inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
    # Primer día de este mes
    inicio_mes = hoy.replace(day=1)

    ventas = Venta.objects.filter(negocio__slug=negocio_slug).prefetch_related('items')

    ventas_hoy = ventas.filter(fecha=hoy)
    ventas_semana = ventas.filter(fecha__gte=inicio_semana)
    ventas_mes = ventas.filter(fecha__gte=inicio_mes)

    def _calcular(qs):
        qs_list = list(qs)
        total = sum(v.total for v in qs_list)
        ganancia = sum(v.ganancia_total for v in qs_list)
        return {
            'total': total,
            'ganancia': ganancia,
            'cantidad': len(qs_list),
        }

    return {
        'hoy': _calcular(ventas_hoy),
        'semana': _calcular(ventas_semana),
        'mes': _calcular(ventas_mes),
    }
