"""
Capa de servicios para la lógica CRUD de Productos, Negocios y Ventas.
Las vistas delegan toda la lógica de datos a este módulo.
"""
from decimal import Decimal
import json
import re
from .models import Negocio, Producto, ImagenProducto, Venta, ItemVenta, Insumo, Pedido, ItemPedido, Subcategoria, EventoAnalytics


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
    return (
        Producto.objects
        .filter(negocio__slug=negocio_slug)
        .select_related('negocio', 'categoria', 'subcategoria')
    )


def get_producto(pk: int) -> Producto | None:
    """Retorna un producto por su PK, o None si no existe."""
    try:
        return Producto.objects.select_related('negocio').get(pk=pk)
    except Producto.DoesNotExist:
        return None


def crear_producto(negocio: Negocio, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None, categoria_id: int = None, subcategoria_id: int = None, imagenes_extra=None, colores=None) -> Producto:
    """Crea y retorna un nuevo producto para el negocio dado."""
    producto = Producto.objects.create(
        negocio=negocio,
        categoria_id=categoria_id,
        subcategoria_id=subcategoria_id,
        nombre=nombre,
        precio=precio,
        costo=costo,
        descripcion=descripcion,
        stock=stock,
        imagen=imagen,
        colores=colores or [],
    )
    # Guardar imágenes adicionales
    if imagenes_extra:
        for idx, img in enumerate(imagenes_extra):
            if img:
                ImagenProducto.objects.create(producto=producto, imagen=img, orden=idx)
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


def actualizar_producto(pk: int, nombre: str, precio, costo=0, descripcion: str = '', stock: int = 0, imagen=None, categoria_id: int = None, subcategoria_id: int = None, imagenes_extra=None, imagenes_eliminar=None, quitar_imagen_principal=False, colores=None) -> Producto | None:
    """Actualiza un producto existente. Si el stock aumenta, registra un movimiento de compra."""
    producto = get_producto(pk)
    if producto is None:
        return None

    stock_anterior = producto.stock  # Guardar antes de actualizar

    producto.categoria_id = categoria_id
    producto.subcategoria_id = subcategoria_id
    producto.nombre = nombre
    producto.precio = precio
    producto.costo = costo
    producto.descripcion = descripcion
    producto.stock = stock
    if imagen:
        producto.imagen = imagen
    elif quitar_imagen_principal:
        producto.imagen = None
    producto.colores = colores or []
    producto.save()

    # Eliminar imágenes extra marcadas para borrar
    if imagenes_eliminar:
        ImagenProducto.objects.filter(pk__in=imagenes_eliminar, producto=producto).delete()

    # Agregar nuevas imágenes extra
    if imagenes_extra:
        base_orden = producto.imagenes.count()
        for idx, img in enumerate(imagenes_extra):
            if img:
                ImagenProducto.objects.create(producto=producto, imagen=img, orden=base_orden + idx)

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


def sanitizar_colores(raw) -> list:
    """Convierte el JSON de colores del formulario en una lista limpia de hex.

    Acepta strings del tipo '["#ff0000","#00ff00"]' (o parseable). Valida formato
    #RRGGBB, normaliza a minúsculas, elimina duplicados y limita a 20 colores.
    Un JSON vacío o inválido devuelve [] (producto sin color).
    """
    if not raw:
        return []
    try:
        if isinstance(raw, str):
            valores = json.loads(raw)
        else:
            valores = list(raw)
    except (ValueError, TypeError):
        return []
    hex_re = re.compile(r'^#[0-9a-fA-F]{6}$')
    colores = []
    for v in valores:
        hex_code = str(v).strip().lower()
        if hex_re.match(hex_code) and hex_code not in colores:
            colores.append(hex_code)
        if len(colores) >= 20:
            break
    return colores


def sanitizar_color(raw) -> str | None:
    """Convierte un único valor en un hex #rrggbb válido, o None si no lo es."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raw = str(raw)
    hex_re = re.compile(r'^#[0-9a-fA-F]{6}$')
    color = raw.strip().lower()
    return color if hex_re.match(color) else None


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
    # Un carrito con N productos no debe disparar N consultas. Conservamos el
    # orden de la sesión, pero resolvemos todos los productos de una vez.
    producto_ids = [int(pk) for pk in carrito if str(pk).isdigit()]
    productos = Producto.objects.in_bulk(producto_ids)
    for pk_str, cantidad in carrito.items():
        producto = productos.get(int(pk_str)) if str(pk_str).isdigit() else None
        if producto:
            subtotal = Decimal(str(producto.precio)) * cantidad
            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'es_libre': False,
                'id_str': str(producto.pk),
            })
            
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


def registrar_visita(negocio: Negocio, session: dict) -> None:
    """Registra una visita a la tienda pública una sola vez por sesión."""
    key = f'visita_registrada_{negocio.slug}'
    if not session.get(key):
        EventoAnalytics.objects.create(negocio=negocio, tipo='visita')
        session[key] = True
        session.modified = True


def registrar_busqueda(negocio: Negocio, termino: str) -> None:
    """Registra una búsqueda en la tienda pública."""
    if termino:
        EventoAnalytics.objects.create(
            negocio=negocio,
            tipo='busqueda',
            detalle=termino[:200]
        )


def registrar_click_producto(negocio: Negocio, producto_pk: int) -> None:
    """Registra un clic/vista detallada de un producto."""
    try:
        producto = Producto.objects.get(pk=producto_pk, negocio=negocio)
        EventoAnalytics.objects.create(
            negocio=negocio,
            tipo='click_producto',
            producto=producto
        )
    except Producto.DoesNotExist:
        pass


def get_resumen_estadisticas(negocio_slug: str) -> dict:
    """
    Resumen de estadísticas calculado con agregados SQL en lugar de recorrer
    todas las ventas/productos en Python. Mantiene la misma estructura de salida.
    """
    from django.utils import timezone
    from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
    from django.db.models.functions import ExtractYear, ExtractMonth
    from decimal import Decimal
    import json

    hoy = timezone.now().date()
    # Lunes de esta semana
    inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
    # Primer día de este mes
    inicio_mes = hoy.replace(day=1)
    # Últimos 7 días para métricas online
    hace_7_dias = timezone.now() - timezone.timedelta(days=7)
    hace_30_dias = timezone.now() - timezone.timedelta(days=30)
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

    negocio_id = Negocio.objects.filter(slug=negocio_slug).values_list('pk', flat=True).first()

    def _stats_vacio():
        vacio = {'total': 0, 'ganancia': 0, 'gastos': 0, 'cantidad': 0}
        return {
            'hoy': dict(vacio),
            'semana': dict(vacio),
            'mes': dict(vacio),
            'grafico_labels': json.dumps([]),
            'grafico_gastos': json.dumps([]),
            'grafico_ganancias': json.dumps([]),
            'visitas_semana': 0,
            'pedidos_online_semana': 0,
            'top_busquedas': [],
            'top_clicks': [],
        }

    if negocio_id is None:
        return _stats_vacio()

    ventas_qs = Venta.objects.filter(negocio_id=negocio_id)
    items_qs = ItemVenta.objects.filter(venta__negocio_id=negocio_id)
    productos_qs = Producto.objects.filter(negocio_id=negocio_id)
    eventos = EventoAnalytics.objects.filter(negocio_id=negocio_id)

    def _métricas_periodo(fecha_exacta=None, fecha_min=None, productos_filtro=None):
        v = ventas_qs
        if fecha_exacta is not None:
            v = v.filter(fecha=fecha_exacta)
        elif fecha_min is not None:
            v = v.filter(fecha__gte=fecha_min)

        agg = v.aggregate(total=Sum('total'), cantidad=Count('id'))
        total = agg['total'] or Decimal('0')
        cantidad = agg['cantidad'] or 0

        it = items_qs
        if fecha_exacta is not None:
            it = it.filter(venta__fecha=fecha_exacta)
        elif fecha_min is not None:
            it = it.filter(venta__fecha__gte=fecha_min)
        ganancia = it.aggregate(
            val=Sum(
                F('cantidad') * (F('precio_unitario') - F('costo_unitario')),
                output_field=DecimalField(),
            )
        )['val'] or Decimal('0')

        gastos_ventas = total - ganancia

        prods = productos_qs.filter(**productos_filtro) if productos_filtro else productos_qs.none()
        gastos_inventario = prods.aggregate(
            val=Sum(ExpressionWrapper(F('costo') * F('stock'), output_field=DecimalField()))
        )['val'] or Decimal('0')

        return {
            'total': float(total),
            'ganancia': float(ganancia),
            'gastos': float(gastos_ventas + gastos_inventario),
            'cantidad': cantidad,
        }

    # Gráfico de 6 meses: últimos 6 meses incluyendo el actual
    keys_ordenadas = []
    grafico_labels = []
    for i in range(5, -1, -1):
        y = hoy.year
        m = hoy.month - i
        while m <= 0:
            m += 12
            y -= 1
        keys_ordenadas.append((y, m))
        grafico_labels.append(f"{nombres_meses[m - 1]} {y}")

    fecha_min_grafico = hoy.replace(year=keys_ordenadas[0][0], month=keys_ordenadas[0][1], day=1)

    ventas_por_mes = {
        (r['año'], r['mes']): r
        for r in (
            ventas_qs
            .filter(fecha__gte=fecha_min_grafico)
            .annotate(año=ExtractYear('fecha'), mes=ExtractMonth('fecha'))
            .values('año', 'mes')
            .annotate(total=Sum('total'))
        )
    }
    ganancia_por_mes = {
        (r['año'], r['mes']): r['ganancia']
        for r in (
            items_qs
            .filter(venta__fecha__gte=fecha_min_grafico)
            .annotate(año=ExtractYear('venta__fecha'), mes=ExtractMonth('venta__fecha'))
            .values('año', 'mes')
            .annotate(ganancia=Sum(
                F('cantidad') * (F('precio_unitario') - F('costo_unitario')),
                output_field=DecimalField(),
            ))
        )
    }
    inv_por_mes = {
        (r['año'], r['mes']): r['inv']
        for r in (
            productos_qs
            .filter(creado__date__gte=fecha_min_grafico)
            .annotate(año=ExtractYear('creado'), mes=ExtractMonth('creado'))
            .values('año', 'mes')
            .annotate(inv=Sum(ExpressionWrapper(F('costo') * F('stock'), output_field=DecimalField())))
        )
    }

    grafico_gastos = []
    grafico_ganancias = []
    for key in keys_ordenadas:
        fila_ventas = ventas_por_mes.get(key) or {}
        total_mes = fila_ventas.get('total') or Decimal('0')
        ganancia_mes = ganancia_por_mes.get(key) or Decimal('0')
        gastos_inv_mes = inv_por_mes.get(key) or Decimal('0')
        gastos_mes = (total_mes - ganancia_mes) + gastos_inv_mes
        grafico_gastos.append(float(gastos_mes))
        grafico_ganancias.append(float(ganancia_mes))

    # ── Métricas de tienda online (últimos 7 días) ──
    visitas_semana = eventos.filter(tipo='visita', fecha__gte=hace_7_dias).count()
    pedidos_online_semana = Pedido.objects.filter(
        negocio_id=negocio_id, creado__gte=hace_7_dias
    ).count()

    # Top 5 búsquedas (últimos 30 días)
    top_busquedas = (
        eventos
        .filter(tipo='busqueda', fecha__gte=hace_30_dias)
        .exclude(detalle='')
        .values('detalle')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # Top 5 productos más vistos (últimos 30 días)
    top_clicks = (
        eventos
        .filter(tipo='click_producto', fecha__gte=hace_30_dias)
        .exclude(producto__isnull=True)
        .values('producto__pk', 'producto__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    return {
        'hoy':      _métricas_periodo(fecha_exacta=hoy, productos_filtro={'creado__date': hoy}),
        'semana':   _métricas_periodo(fecha_min=inicio_semana, productos_filtro={'creado__date__gte': inicio_semana}),
        'mes':      _métricas_periodo(fecha_min=inicio_mes, productos_filtro={'creado__date__gte': inicio_mes}),
        'grafico_labels': json.dumps(grafico_labels),
        'grafico_gastos': json.dumps(grafico_gastos),
        'grafico_ganancias': json.dumps(grafico_ganancias),
        # Métricas online
        'visitas_semana': visitas_semana,
        'pedidos_online_semana': pedidos_online_semana,
        'top_busquedas': list(top_busquedas),
        'top_clicks': list(top_clicks),
    }


# ── Pedidos de Clientes (Catálogo Público) ────────────────────────────────

def get_pedidos(negocio_slug: str):
    """Retorna todos los pedidos de un negocio, ordenados por fecha descendente."""
    return (
        Pedido.objects
        .filter(negocio__slug=negocio_slug)
        .order_by('-creado')
        .prefetch_related('items__producto')
    )

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
            color=sanitizar_color(item.get('color')),
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
            color=item.color,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            costo_unitario=item.producto.costo if item.producto else 0
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

def _normalizar_carrito_publico(carrito: dict) -> dict:
    """Convierte el formato legacy {pk: cantidad} a {pk: {'cantidad': n, 'color': hex|None}}."""
    norm = {}
    for pk_str, valor in (carrito or {}).items():
        if isinstance(valor, dict):
            cantidad = int(valor.get('cantidad', 0) or 0)
            color = sanitizar_color(valor.get('color'))
            if cantidad > 0:
                norm[str(pk_str)] = {'cantidad': cantidad, 'color': color}
        else:
            try:
                cantidad = int(valor)
            except (TypeError, ValueError):
                cantidad = 0
            if cantidad > 0:
                norm[str(pk_str)] = {'cantidad': cantidad, 'color': None}
    return norm

def get_carrito_publico(session: dict) -> dict:
    return _normalizar_carrito_publico(session.get('carrito_publico', {}))

def carrito_publico_cantidad(carrito: dict, producto_pk: int) -> int:
    """Cantidad acumulada de un producto en el carrito público (soporta formato legacy)."""
    linea = _normalizar_carrito_publico(carrito).get(str(producto_pk))
    return linea['cantidad'] if linea else 0

def carrito_publico_agregar(session: dict, producto_pk: int, color: str | None = None) -> None:
    """Agrega 1 unidad del producto (opcionalmente con un color) al carrito de la sesión."""
    carrito = _normalizar_carrito_publico(session.get('carrito_publico', {}))
    key = str(producto_pk)
    linea = carrito.get(key, {'cantidad': 0, 'color': None})
    linea['cantidad'] += 1
    if color is not None:
        linea['color'] = sanitizar_color(color)
    carrito[key] = linea
    session['carrito_publico'] = carrito
    session.modified = True

def carrito_publico_color(session: dict, producto_pk: int, color: str | None) -> None:
    """Actualiza el color de una línea existente del carrito público."""
    carrito = _normalizar_carrito_publico(session.get('carrito_publico', {}))
    key = str(producto_pk)
    if key in carrito:
        carrito[key]['color'] = sanitizar_color(color)
        session['carrito_publico'] = carrito
        session.modified = True

def carrito_publico_quitar(session: dict, producto_pk: int) -> None:
    """Elimina completamente el producto del carrito (sin importar cantidad)."""
    carrito = _normalizar_carrito_publico(session.get('carrito_publico', {}))
    carrito.pop(str(producto_pk), None)
    session['carrito_publico'] = carrito
    session.modified = True

def carrito_publico_decrementar(session: dict, producto_pk: int) -> None:
    """Descuenta 1 unidad. Si llega a 0, elimina el item del carrito."""
    carrito = _normalizar_carrito_publico(session.get('carrito_publico', {}))
    key = str(producto_pk)
    if key in carrito:
        carrito[key]['cantidad'] -= 1
        if carrito[key]['cantidad'] <= 0:
            del carrito[key]
    session['carrito_publico'] = carrito
    session.modified = True

def carrito_publico_limpiar(session: dict) -> None:
    session['carrito_publico'] = {}
    session.modified = True

def get_carrito_publico_detalle(session: dict, negocio_slug: str) -> list[dict]:
    carrito = get_carrito_publico(session)
    items = []
    producto_ids = [int(pk) for pk in carrito if str(pk).isdigit()]
    productos = Producto.objects.filter(pk__in=producto_ids, negocio__slug=negocio_slug).in_bulk()
    for pk_str, linea in carrito.items():
        try:
            # Asegurarse de que el producto pertenezca a la tienda que se está viendo
            producto = productos.get(int(pk_str)) if str(pk_str).isdigit() else None
            if producto is None:
                continue
            cantidad = linea['cantidad']
            subtotal = Decimal(str(producto.precio)) * cantidad
            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'color': linea['color'],
            })
        except Producto.DoesNotExist:
            pass
    return items

def carrito_publico_total(session: dict, negocio_slug: str) -> Decimal:
    return sum(item['subtotal'] for item in get_carrito_publico_detalle(session, negocio_slug)) or Decimal('0')
