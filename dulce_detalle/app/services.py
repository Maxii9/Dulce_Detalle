"""
Capa de servicios para la lógica CRUD de Productos, Negocios y Ventas.
Las vistas delegan toda la lógica de datos a este módulo.
"""
from decimal import Decimal
from .models import Negocio, Producto, Venta, ItemVenta, Insumo, Pedido, ItemPedido


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


def crear_producto(negocio: Negocio, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None, categoria_id: int = None) -> Producto:
    """Crea y retorna un nuevo producto para el negocio dado."""
    producto = Producto.objects.create(
        negocio=negocio,
        categoria_id=categoria_id,
        nombre=nombre,
        precio=precio,
        costo=costo,
        descripcion=descripcion,
        stock=stock,
        imagen=imagen,
    )
    # Si el producto se crea con stock inicial > 0, registrar movimiento de compra
    if stock > 0:
        from django.utils import timezone
        from decimal import Decimal
        total_egreso = Decimal(str(costo)) * stock
        Venta.objects.create(
            negocio=negocio,
            fecha=timezone.localdate(),
            tipo='pagada',
            metodo_pago='egreso',
            total=-total_egreso,
            tipo_movimiento='compra_stock',
            observacion=f'Stock inicial: {stock} unidad(es) de "{nombre}"',
        )
    return producto


def actualizar_producto(pk: int, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None, categoria_id: int = None) -> Producto | None:
    """Actualiza un producto existente. Si el stock aumenta, registra un movimiento de compra."""
    producto = get_producto(pk)
    if producto is None:
        return None

    stock_anterior = producto.stock  # Guardar antes de actualizar

    producto.categoria_id = categoria_id
    producto.nombre = nombre
    producto.precio = precio
    producto.costo = costo
    producto.descripcion = descripcion
    producto.stock = stock
    if imagen:
        producto.imagen = imagen
    producto.save()

    # Registrar movimiento de compra si el stock aumentó
    delta = stock - stock_anterior
    if delta > 0:
        from django.utils import timezone
        total_egreso = Decimal(str(costo)) * delta
        Venta.objects.create(
            negocio=producto.negocio,
            fecha=timezone.localdate(),
            tipo='pagada',
            metodo_pago='egreso',
            total=-total_egreso,
            tipo_movimiento='compra_stock',
            observacion=f'Reposición de stock: +{delta} unidad(es) de "{nombre}"',
        )

    return producto



def eliminar_producto(pk: int) -> bool:
    """Elimina un producto por PK. Retorna True si fue eliminado, False si no existía."""
    producto = get_producto(pk)
    if producto is None:
        return False
    producto.delete()
    return True


def get_top_vendidos(negocio_slug: str, limite: int = 5) -> list:
    """Retorna una lista con los PKs de los N productos más vendidos del negocio."""
    from django.db.models import Sum
    top = (
        ItemVenta.objects
        .filter(venta__negocio__slug=negocio_slug)
        .values('producto_id')
        .annotate(total=Sum('cantidad'))
        .order_by('-total')[:limite]
    )
    return [item['producto_id'] for item in top]


# ── Insumos (Calculadora de Costos) ───────────────────────────────────────

def get_insumos(negocio_slug: str):
    """Lista todos los insumos de un negocio dado su slug."""
    return Insumo.objects.filter(negocio__slug=negocio_slug)


def get_insumo(pk: int) -> Insumo | None:
    """Retorna un insumo por su PK, o None si no existe."""
    try:
        return Insumo.objects.get(pk=pk)
    except Insumo.DoesNotExist:
        return None


def crear_insumo(negocio: Negocio, nombre: str, costo_unitario) -> Insumo:
    """Crea y retorna un nuevo insumo para el negocio dado."""
    return Insumo.objects.create(
        negocio=negocio,
        nombre=nombre,
        costo_unitario=costo_unitario
    )


def actualizar_insumo(pk: int, nombre: str, costo_unitario) -> Insumo | None:
    """Actualiza un insumo existente. Retorna el insumo actualizado o None."""
    insumo = get_insumo(pk)
    if insumo is None:
        return None
    insumo.nombre = nombre
    insumo.costo_unitario = costo_unitario
    insumo.save()
    return insumo


def eliminar_insumo(pk: int) -> bool:
    """Elimina un insumo por PK. Retorna True si fue eliminado, False si no existía."""
    insumo = get_insumo(pk)
    if insumo is None:
        return False
    insumo.delete()
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
    session['carrito_libre'] = []
    session.modified = True

def get_carrito_libre(session: dict) -> list[dict]:
    """Retorna la lista de ítems libres"""
    return session.get('carrito_libre', [])

def carrito_libre_agregar(session: dict, nombre: str, precio: float, costo: float, cantidad: int, es_gasto: bool = False) -> None:
    carrito = get_carrito_libre(session)
    import uuid
    id_libre = str(uuid.uuid4())
    carrito.append({
        'id_libre': id_libre,
        'nombre': nombre,
        'precio': precio,
        'costo': costo,
        'cantidad': cantidad,
        'es_gasto': es_gasto,
    })
    session['carrito_libre'] = carrito
    session.modified = True

def carrito_libre_quitar(session: dict, id_libre: str) -> None:
    carrito = get_carrito_libre(session)
    carrito = [item for item in carrito if item['id_libre'] != id_libre]
    session['carrito_libre'] = carrito
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
            items.append({
                'producto': producto, 
                'cantidad': cantidad, 
                'subtotal': subtotal,
                'es_libre': False,
                'id_str': str(producto.pk),
            })
        except Producto.DoesNotExist:
            pass
            
    carrito_libre = get_carrito_libre(session)
    for lib in carrito_libre:
        es_gasto = lib.get('es_gasto', False)
        precio_val = Decimal(str(lib['precio']))
        subtotal = precio_val * int(lib['cantidad'])
        if es_gasto:
            subtotal = -subtotal
        items.append({
            'producto': None,
            'nombre_libre': lib['nombre'],
            'precio_libre': precio_val,
            'costo_libre': Decimal(str(lib['costo'])),
            'cantidad': lib['cantidad'],
            'subtotal': subtotal,
            'es_libre': True,
            'es_gasto': es_gasto,
            'id_str': lib['id_libre'],
        })
    return items


def carrito_total(session: dict) -> Decimal:
    """Calcula el total del carrito."""
    return sum(item['subtotal'] for item in get_carrito_detalle(session)) or Decimal('0')


# ── Ventas ────────────────────────────────────────────────────────────────

def get_ventas(negocio_slug: str):
    """Lista todas las ventas de un negocio."""
    return Venta.objects.filter(negocio__slug=negocio_slug).prefetch_related('items__producto')


def crear_venta(negocio: Negocio, fecha, tipo: str, metodo_pago: str, items_data: list, observacion: str = '') -> Venta:
    """
    Crea una venta con sus items.
    items_data: lista de dicts (puede contener productos reales o libres)
    """
    total = sum(item['subtotal'] for item in items_data)
    venta = Venta.objects.create(
        negocio=negocio,
        fecha=fecha,
        tipo=tipo,
        metodo_pago=metodo_pago,
        total=total,
        observacion=observacion,
    )
    for item in items_data:
        if item.get('es_libre'):
            es_gasto = item.get('es_gasto', False)
            # Para gastos: precio negativo, tipo_movimiento=compra_stock
            precio_ui = item['precio_libre']  # siempre positivo en el item
            ItemVenta.objects.create(
                venta=venta,
                producto=None,
                nombre_libre=item['nombre_libre'],
                cantidad=item['cantidad'],
                precio_unitario=precio_ui,
                costo_unitario=item['costo_libre'],
            )
            if es_gasto:
                venta.tipo_movimiento = 'compra_stock'
                venta.metodo_pago = 'egreso'
                venta.save(update_fields=['tipo_movimiento', 'metodo_pago'])
        else:
            ItemVenta.objects.create(
                venta=venta,
                producto=item['producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['producto'].precio,
                costo_unitario=item['producto'].costo,
            )
            # Reducir stock
            prod = item['producto']
            prod.stock -= item['cantidad']
            prod.save()
    return venta


def eliminar_ventas(venta_ids: list) -> int:
    """
    Elimina múltiples ventas por sus IDs.
    No restituye el stock (los productos vendidos simplemente se eliminan del historial de ventas).
    """
    ventas = Venta.objects.filter(pk__in=venta_ids)
    count = 0
    for venta in ventas:
        venta.delete()
        count += 1
    return count


def get_resumen_estadisticas(negocio_slug: str) -> dict:
    from django.utils import timezone
    import json
    hoy = timezone.now().date()
    # Lunes de esta semana
    inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
    # Primer día de este mes
    inicio_mes = hoy.replace(day=1)

    ventas = Venta.objects.filter(negocio__slug=negocio_slug).prefetch_related('items')
    productos = Producto.objects.filter(negocio__slug=negocio_slug)

    ventas_hoy = ventas.filter(fecha=hoy)
    ventas_semana = ventas.filter(fecha__gte=inicio_semana)
    ventas_mes = ventas.filter(fecha__gte=inicio_mes)

    def _calcular(qs_ventas, is_hoy=False, is_semana=False, is_mes=False):
        qs_list = list(qs_ventas)
        total = sum(v.total for v in qs_list)
        ganancia = sum(v.ganancia_total for v in qs_list)
        gastos_ventas = total - ganancia

        if is_hoy:
            prods = productos.filter(creado__date=hoy)
        elif is_semana:
            prods = productos.filter(creado__date__gte=inicio_semana)
        elif is_mes:
            prods = productos.filter(creado__date__gte=inicio_mes)
        else:
            prods = productos.none()

        gastos_inventario = sum(p.costo * p.stock for p in prods)
        
        return {
            'total': float(total),
            'ganancia': float(ganancia),
            'gastos': float(gastos_ventas + gastos_inventario),
            'cantidad': len(qs_list),
        }

    # Gráfico de 6 meses
    grafico_labels = []
    grafico_gastos = []
    grafico_ganancias = []

    for i in range(5, -1, -1):
        y = hoy.year
        m = hoy.month - i
        while m <= 0:
            m += 12
            y -= 1
        
        ventas_mes_i = [v for v in ventas if v.fecha.year == y and v.fecha.month == m]
        prods_mes_i = [p for p in productos if p.creado.year == y and p.creado.month == m]
        
        total_cobrado = sum(v.total for v in ventas_mes_i)
        ganancia_neta = sum(v.ganancia_total for v in ventas_mes_i)
        gastos_ventas = total_cobrado - ganancia_neta
        gastos_inventario = sum(p.costo * p.stock for p in prods_mes_i)
        
        gastos = gastos_ventas + gastos_inventario
        
        nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        nombre_mes = f"{nombres_meses[m-1]} {y}"
        
        grafico_labels.append(nombre_mes)
        grafico_gastos.append(float(gastos))
        grafico_ganancias.append(float(ganancia_neta))

    return {
        'hoy': _calcular(ventas_hoy, is_hoy=True),
        'semana': _calcular(ventas_semana, is_semana=True),
        'mes': _calcular(ventas_mes, is_mes=True),
        'grafico_labels': json.dumps(grafico_labels),
        'grafico_gastos': json.dumps(grafico_gastos),
        'grafico_ganancias': json.dumps(grafico_ganancias),
    }


# ── Pedidos de Clientes (Catálogo Público) ────────────────────────────────

def get_pedidos(negocio_slug: str):
    """Retorna todos los pedidos de un negocio, ordenados por fecha descendente."""
    return Pedido.objects.filter(negocio__slug=negocio_slug).prefetch_related('items__producto')

def get_pedidos_pendientes_count(negocio_slug: str) -> int:
    return Pedido.objects.filter(negocio__slug=negocio_slug, estado='pendiente').count()

def crear_pedido_cliente(negocio: Negocio, nombre: str, telefono: str, direccion: str, items_data: list) -> Pedido:
    """Crea un pedido desde la tienda pública."""
    total = sum(Decimal(str(item['producto'].precio)) * item['cantidad'] for item in items_data)
    pedido = Pedido.objects.create(
        negocio=negocio,
        cliente_nombre=nombre,
        cliente_telefono=telefono,
        cliente_direccion=direccion,
        total=total
    )
    for item in items_data:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=item['producto'],
            nombre_producto=item['producto'].nombre,
            cantidad=item['cantidad'],
            precio_unitario=item['producto'].precio
        )
    return pedido

def aceptar_pedido(pk: int) -> bool:
    """Marca como aceptado, descuenta stock y crea una Venta oficial."""
    from django.utils import timezone
    try:
        pedido = Pedido.objects.get(pk=pk, estado='pendiente')
    except Pedido.DoesNotExist:
        return False

    # Descontar stock
    for item in pedido.items.all():
        producto = item.producto
        producto.stock -= item.cantidad
        if producto.stock < 0:
            producto.stock = 0
        producto.save()

    # Transforma en venta
    venta = Venta.objects.create(
        negocio=pedido.negocio,
        fecha=timezone.localdate(),
        tipo='pagada',
        metodo_pago='otro', # O podría agregarse como 'pedido_online'
        total=pedido.total
    )
    for item in pedido.items.all():
        ItemVenta.objects.create(
            venta=venta,
            producto=item.producto,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            costo_unitario=item.producto.costo
        )

    pedido.estado = 'aceptado'
    pedido.save()
    return True

def eliminar_pedido(pk: int) -> bool:
    """Elimina el pedido, sirve también para rechazarlo."""
    try:
        pedido = Pedido.objects.get(pk=pk)
        pedido.delete()
        return True
    except Pedido.DoesNotExist:
        return False


# ── Carrito Público (session-based) ───────────────────────────────────────

def get_carrito_publico(session: dict) -> dict:
    return session.get('carrito_publico', {})

def carrito_publico_agregar(session: dict, producto_pk: int) -> None:
    carrito = session.get('carrito_publico', {})
    key = str(producto_pk)
    carrito[key] = carrito.get(key, 0) + 1
    session['carrito_publico'] = carrito
    session.modified = True

def carrito_publico_quitar(session: dict, producto_pk: int) -> None:
    carrito = session.get('carrito_publico', {})
    carrito.pop(str(producto_pk), None)
    session['carrito_publico'] = carrito
    session.modified = True

def carrito_publico_limpiar(session: dict) -> None:
    session['carrito_publico'] = {}
    session.modified = True

def get_carrito_publico_detalle(session: dict, negocio_slug: str) -> list[dict]:
    carrito = get_carrito_publico(session)
    items = []
    for pk_str, cantidad in carrito.items():
        try:
            # Asegurarse de que el producto pertenezca a la tienda que se está viendo
            producto = Producto.objects.get(pk=int(pk_str), negocio__slug=negocio_slug)
            subtotal = Decimal(str(producto.precio)) * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
        except Producto.DoesNotExist:
            pass
    return items

def carrito_publico_total(session: dict, negocio_slug: str) -> Decimal:
    return sum(item['subtotal'] for item in get_carrito_publico_detalle(session, negocio_slug)) or Decimal('0')
