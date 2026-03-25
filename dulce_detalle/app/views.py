from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from . import services


def _contexto_base(request):
    """Contexto compartido con datos del negocio activo."""
    negocio = services.get_negocio_activo(request.session)
    negocios = services.get_negocios()
    return negocio, negocios


def inicio(request):
    return redirect('lista_productos')


def cambiar_negocio(request, slug):
    """Guarda el negocio activo en la sesión."""
    negocio = get_object_or_404(services.Negocio, slug=slug)
    request.session['negocio_slug'] = negocio.slug
    return redirect('lista_productos')


def lista_productos(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return render(request, 'productos/sin_negocio.html', {'negocios': negocios})
    productos = services.get_productos(negocio.slug)
    
    query = request.GET.get('q', '').strip()
    if query:
        productos = productos.filter(nombre__icontains=query)
        
    valor_inventario = sum(p.costo * p.stock for p in productos)

    return render(request, 'productos/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'productos': productos,
        'query': query,
        'valor_inventario': valor_inventario,
    })


def crear_producto(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        costo = request.POST.get('costo', '0')
        descripcion = request.POST.get('descripcion', '').strip()
        stock = request.POST.get('stock', '0')
        imagen = request.FILES.get('imagen')
        if nombre and precio:
            try:
                services.crear_producto(
                    negocio=negocio,
                    nombre=nombre,
                    precio=float(precio),
                    costo=float(costo),
                    descripcion=descripcion,
                    stock=int(stock),
                    imagen=imagen,
                )
                messages.success(request, f'Producto "{nombre}" creado exitosamente.')
                return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Precio, costo o stock inválidos.')
        else:
            messages.error(request, 'Nombre y precio son obligatorios.')

    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo producto',
        'producto': None,
    })


def editar_producto(request, pk):
    negocio, negocios = _contexto_base(request)
    producto = get_object_or_404(services.Producto, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        costo = request.POST.get('costo', '0')
        descripcion = request.POST.get('descripcion', '').strip()
        stock = request.POST.get('stock', '0')
        imagen = request.FILES.get('imagen')
        if nombre and precio:
            try:
                services.actualizar_producto(
                    pk=pk,
                    nombre=nombre,
                    precio=float(precio),
                    costo=float(costo),
                    descripcion=descripcion,
                    stock=int(stock),
                    imagen=imagen,
                )
                messages.success(request, f'Producto "{nombre}" actualizado.')
                return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Precio, costo o stock inválidos.')
        else:
            messages.error(request, 'Nombre y precio son obligatorios.')

    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar producto',
        'producto': producto,
    })


def eliminar_producto(request, pk):
    negocio, negocios = _contexto_base(request)
    producto = get_object_or_404(services.Producto, pk=pk)

    if request.method == 'POST':
        nombre = producto.nombre
        services.eliminar_producto(pk)
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect('lista_productos')

    return render(request, 'productos/confirmar_eliminar.html', {
        'negocio': negocio,
        'negocios': negocios,
        'producto': producto,
    })


# ── Carrito ────────────────────────────────────────────────────────────────

def carrito_agregar(request, pk):
    """Agrega un producto al carrito y vuelve a la lista de productos."""
    services.carrito_agregar(request.session, pk)
    return redirect('lista_productos')


def carrito_quitar(request, pk):
    """Quita un producto del carrito."""
    services.carrito_quitar(request.session, pk)
    return redirect('nueva_venta')


def carrito_limpiar(request):
    """Vacía el carrito."""
    services.carrito_limpiar(request.session)
    return redirect('lista_productos')


# ── Ventas ─────────────────────────────────────────────────────────────────

def lista_ventas(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
    ventas = services.get_ventas(negocio.slug)

    # Filtros
    fecha = request.GET.get('fecha', '')
    metodo = request.GET.get('metodo', '')
    if fecha:
        ventas = ventas.filter(fecha=fecha)
    if metodo:
        ventas = ventas.filter(metodo_pago=metodo)

    return render(request, 'ventas/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'ventas': ventas,
        'filtro_fecha': fecha,
        'filtro_metodo': metodo,
        'carrito_count': len(services.get_carrito(request.session)),
    })


def nueva_venta(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')

    carrito_items = services.get_carrito_detalle(request.session)
    total = services.carrito_total(request.session)

    if request.method == 'POST':
        if not carrito_items:
            messages.error(request, 'El carrito está vacío.')
            return redirect('lista_productos')

        fecha = request.POST.get('fecha', str(timezone.localdate()))
        tipo = request.POST.get('tipo', 'pagada')
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')

        venta = services.crear_venta(
            negocio=negocio,
            fecha=fecha,
            tipo=tipo,
            metodo_pago=metodo_pago,
            items_data=carrito_items,
        )
        services.carrito_limpiar(request.session)
        messages.success(request, f'Venta #{venta.pk} registrada por ${venta.total}.')
        return redirect('lista_ventas')

    return render(request, 'ventas/crear.html', {
        'negocio': negocio,
        'negocios': negocios,
        'carrito_items': carrito_items,
        'total': total,
        'hoy': timezone.localdate(),
        'carrito_count': len(carrito_items),
    })


def estadisticas_ventas(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')

    stats = services.get_resumen_estadisticas(negocio.slug)

    return render(request, 'ventas/estadisticas.html', {
        'negocio': negocio,
        'negocios': negocios,
        'stats': stats,
        'carrito_count': len(services.get_carrito(request.session)),
    })


# ── Calculadora de Costos ──────────────────────────────────────────────────

def calculadora_costos(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
    
    insumos = services.get_insumos(negocio.slug)
    
    return render(request, 'calculadora/index.html', {
        'negocio': negocio,
        'negocios': negocios,
        'insumos': insumos,
        'carrito_count': len(services.get_carrito(request.session)),
    })


def crear_insumo(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('calculadora_costos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        costo_unitario = request.POST.get('costo_unitario', '0')
        if nombre and costo_unitario:
            try:
                services.crear_insumo(
                    negocio=negocio,
                    nombre=nombre,
                    costo_unitario=float(costo_unitario)
                )
                messages.success(request, f'Insumo "{nombre}" creado exitosamente.')
                return redirect('calculadora_costos')
            except ValueError:
                messages.error(request, 'Costo unitario inválido.')
        else:
            messages.error(request, 'El nombre y costo son obligatorios.')

    return render(request, 'calculadora/form_insumo.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo insumo',
        'insumo': None,
        'carrito_count': len(services.get_carrito(request.session)),
    })


def editar_insumo(request, pk):
    negocio, negocios = _contexto_base(request)
    insumo = get_object_or_404(services.Insumo, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        costo_unitario = request.POST.get('costo_unitario', '0')
        if nombre and costo_unitario:
            try:
                services.actualizar_insumo(
                    pk=pk,
                    nombre=nombre,
                    costo_unitario=float(costo_unitario)
                )
                messages.success(request, f'Insumo "{nombre}" actualizado.')
                return redirect('calculadora_costos')
            except ValueError:
                messages.error(request, 'Costo unitario inválido.')
        else:
            messages.error(request, 'El nombre y costo son obligatorios.')

    return render(request, 'calculadora/form_insumo.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar insumo',
        'insumo': insumo,
        'carrito_count': len(services.get_carrito(request.session)),
    })


def eliminar_insumo(request, pk):
    negocio, negocios = _contexto_base(request)
    insumo = get_object_or_404(services.Insumo, pk=pk)

    if request.method == 'POST':
        nombre = insumo.nombre
        services.eliminar_insumo(pk)
        messages.success(request, f'Insumo "{nombre}" eliminado.')
        return redirect('calculadora_costos')

    return render(request, 'calculadora/confirmar_eliminar_insumo.html', {
        'negocio': negocio,
        'negocios': negocios,
        'insumo': insumo,
        'carrito_count': len(services.get_carrito(request.session)),
    })


# ── Tienda Pública (Clientes) ─────────────────────────────────────────────

def tienda_publica(request, slug):
    negocio = get_object_or_404(services.Negocio, slug=slug)
    productos = services.get_productos(slug)
    
    query = request.GET.get('q', '').strip()
    if query:
        productos = productos.filter(nombre__icontains=query)

    carrito_items = services.get_carrito_publico_detalle(request.session, slug)
    carrito_count = sum(item['cantidad'] for item in carrito_items)

    return render(request, 'tienda_publica/index.html', {
        'negocio': negocio,
        'productos': productos,
        'query': query,
        'carrito_count': carrito_count,
    })

def agregar_carrito_publico(request, slug, pk):
    services.carrito_publico_agregar(request.session, pk)
    return redirect('tienda_publica', slug=slug)

def quitar_carrito_publico(request, slug, pk):
    services.carrito_publico_quitar(request.session, pk)
    return redirect('checkout_publico', slug=slug)

def checkout_publico(request, slug):
    negocio = get_object_or_404(services.Negocio, slug=slug)
    carrito_items = services.get_carrito_publico_detalle(request.session, slug)
    total = services.carrito_publico_total(request.session, slug)

    if not carrito_items:
        return redirect('tienda_publica', slug=slug)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        
        if nombre and telefono:
            pedido = services.crear_pedido_cliente(
                negocio=negocio,
                nombre=nombre,
                telefono=telefono,
                direccion=direccion,
                items_data=carrito_items
            )
            services.carrito_publico_limpiar(request.session)
            return redirect('exito_publico', slug=slug, pedido_id=pedido.pk)

    return render(request, 'tienda_publica/checkout.html', {
        'negocio': negocio,
        'carrito_items': carrito_items,
        'total': total,
    })

def exito_publico(request, slug, pedido_id):
    negocio = get_object_or_404(services.Negocio, slug=slug)
    return render(request, 'tienda_publica/exito.html', {
        'negocio': negocio,
        'pedido_id': pedido_id
    })


# ── Gestión de Pedidos (Administrador) ────────────────────────────────────

def lista_pedidos(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
    
    pedidos = services.get_pedidos(negocio.slug)
    pedidos_pendientes_count = services.get_pedidos_pendientes_count(negocio.slug)

    return render(request, 'pedidos/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'pedidos': pedidos,
        'carrito_count': len(services.get_carrito(request.session)),
        'pedidos_pendientes_count': pedidos_pendientes_count,
    })

def aceptar_pedido(request, pk):
    _negocio, _negocios = _contexto_base(request)
    if request.method == 'POST':
        if services.aceptar_pedido(pk):
            messages.success(request, 'Pedido aceptado y convertido en venta.')
        else:
            messages.error(request, 'No se pudo aceptar el pedido (tal vez ya no está pendiente).')
    return redirect('lista_pedidos')

def eliminar_pedido(request, pk):
    _negocio, _negocios = _contexto_base(request)
    if request.method == 'POST':
        if services.eliminar_pedido(pk):
            messages.success(request, 'Pedido eliminado/rechazado.')
        else:
            messages.error(request, 'No se encontró el pedido.')
    return redirect('lista_pedidos')