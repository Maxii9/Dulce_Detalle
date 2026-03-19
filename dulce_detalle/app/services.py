"""
Capa de servicios para la lógica CRUD de Productos y Negocios.
Las vistas delegan toda la lógica de datos a este módulo.
"""
from .models import Negocio, Producto


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


def crear_producto(negocio: Negocio, nombre: str, precio, descripcion: str = '', stock: int = 0) -> Producto:
    """Crea y retorna un nuevo producto para el negocio dado."""
    return Producto.objects.create(
        negocio=negocio,
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        stock=stock,
    )


def actualizar_producto(pk: int, nombre: str, precio, descripcion: str = '', stock: int = 0) -> Producto | None:
    """Actualiza un producto existente. Retorna el producto actualizado o None."""
    producto = get_producto(pk)
    if producto is None:
        return None
    producto.nombre = nombre
    producto.precio = precio
    producto.descripcion = descripcion
    producto.stock = stock
    producto.save()
    return producto


def eliminar_producto(pk: int) -> bool:
    """Elimina un producto por PK. Retorna True si fue eliminado, False si no existía."""
    producto = get_producto(pk)
    if producto is None:
        return False
    producto.delete()
    return True
