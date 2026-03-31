from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json
from . import services
from .models import Nota
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from app.models import Negocio, CategoriaProducto
import functools

def tienda_requerida(view_func):
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has any store
        if not request.user.negocios.exists():
            return redirect('crear_tienda_inicial')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def _contexto_base(request):
    """Contexto compartido con datos del negocio activo para el usuario."""
    if not request.user.is_authenticated:
        return None, []
    
    negocios = list(request.user.negocios.all())
        
    negocio_slug = request.session.get('negocio_slug')
    negocio = None
    if negocio_slug:
        negocio = next((n for n in negocios if n.slug == negocio_slug), None)
    if not negocio and negocios:
        negocio = negocios[0]
        request.session['negocio_slug'] = negocio.slug
    return negocio, negocios


@tienda_requerida
def inicio(request):
    return redirect('lista_productos')


@tienda_requerida
def cambiar_negocio(request, slug):
    """Guarda el negocio activo en la sesión."""
    negocio = get_object_or_404(services.Negocio, slug=slug)
    request.session['negocio_slug'] = negocio.slug
    return redirect('lista_productos')


@tienda_requerida
def lista_productos(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return render(request, 'productos/sin_negocio.html', {'negocios': negocios})
    productos = services.get_productos(negocio.slug)
    
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    if query:
        productos = productos.filter(nombre__icontains=query)
    if tipo:
        productos = productos.filter(tipo=tipo)
        
    carrito_items = services.get_carrito_detalle(request.session)
    total = services.carrito_total(request.session)
    
    valor_inventario = sum(p.costo * p.stock for p in productos)

    tipos = negocio.categorias_producto.all()

    # PKs de productos cuyo stock ya está agotado en el carrito
    carrito_cantidades = {item['producto'].pk: item['cantidad'] for item in carrito_items}
    carrito_maxed = [pk for pk, cant in carrito_cantidades.items()
                     if cant >= (services.get_producto(pk).stock if services.get_producto(pk) else 0)]
        
    return render(request, 'productos/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'productos': productos,
        'query': query,
        'tipo_activo': tipo,
        'tipos': tipos,
        'carrito_items': carrito_items,
        'total': total,
        'carrito_count': len(carrito_items),
        'valor_inventario': valor_inventario,
        'carrito_maxed': carrito_maxed,
        'carrito_cantidades': carrito_cantidades,
    })


@tienda_requerida
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
        tipo = request.POST.get('tipo', 'otros')
        imagen = request.FILES.get('imagen')
        if nombre and precio:
            try:
                p_val = float(precio)
                c_val = float(costo)
                s_val = int(stock)
                
                if p_val < 0 or c_val < 0 or s_val < 0:
                    messages.error(request, 'Precio, costo y stock no pueden ser negativos.')
                else:
                    services.crear_producto(
                        negocio=negocio,
                        nombre=nombre[:100],
                        precio=p_val,
                        costo=c_val,
                        descripcion=descripcion[:500],
                        stock=s_val,
                        imagen=imagen,
                        tipo=tipo[:50],
                    )
                    messages.success(request, f'Producto "{nombre}" creado exitosamente.')
                    return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Los valores numéricos ingresados no son válidos.')
        else:
            messages.error(request, 'El nombre y el precio son campos obligatorios.')

    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo producto',
        'producto': None,
        'categorias': negocio.categorias_producto.all(),
    })


@tienda_requerida
def editar_producto(request, pk):
    negocio, negocios = _contexto_base(request)
    producto = get_object_or_404(services.Producto, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        costo = request.POST.get('costo', '0')
        descripcion = request.POST.get('descripcion', '').strip()
        stock = request.POST.get('stock', '0')
        tipo = request.POST.get('tipo', 'otros')
        imagen = request.FILES.get('imagen')
        if nombre and precio:
            try:
                p_val = float(precio)
                c_val = float(costo)
                s_val = int(stock)

                if p_val < 0 or c_val < 0 or s_val < 0:
                    messages.error(request, 'Precio, costo y stock no pueden ser negativos.')
                else:
                    services.actualizar_producto(
                        pk=pk,
                        nombre=nombre[:100],
                        precio=p_val,
                        costo=c_val,
                        descripcion=descripcion[:500],
                        stock=s_val,
                        imagen=imagen,
                        tipo=tipo[:50],
                    )
                    messages.success(request, f'Producto "{nombre}" actualizado.')
                    return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Los valores numéricos ingresados no son válidos.')
        else:
            messages.error(request, 'El nombre y el precio son campos obligatorios.')

    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar producto',
        'producto': producto,
        'categorias': negocio.categorias_producto.all(),
    })


@tienda_requerida
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

@tienda_requerida
def carrito_agregar(request, pk):
    """Agrega un producto al carrito solo si hay stock disponible."""
    producto = get_object_or_404(services.Producto, pk=pk)
    carrito = request.session.get('carrito', {})
    cantidad_actual = carrito.get(str(pk), 0)
    if cantidad_actual >= producto.stock:
        messages.warning(request, f'Stock máximo alcanzado para "{producto.nombre}" ({producto.stock} disp.).')
    else:
        services.carrito_agregar(request.session, pk)
    return redirect('lista_productos')


@tienda_requerida
def carrito_quitar(request, pk):
    """Quita un producto del carrito y vuelve a la página anterior."""
    services.carrito_quitar(request.session, pk)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('nueva_venta')


@tienda_requerida
def carrito_limpiar(request):
    """Vacía el carrito."""
    services.carrito_limpiar(request.session)
    return redirect('lista_productos')


@tienda_requerida
def carrito_libre_agregar_view(request):
    """Agrega un producto no registrado al carrito."""
    if request.method == 'POST':
        nombre = request.POST.get('nombre_libre', '').strip()
        precio = request.POST.get('precio_libre', '0').strip() or '0'
        costo = request.POST.get('costo_libre', '0').strip() or '0'
        cantidad = request.POST.get('cantidad_libre', '1').strip() or '1'
        
        try:
            p_val = float(precio)
            c_val = float(costo)
            cant_val = int(cantidad)
            
            if nombre and p_val >= 0 and c_val >= 0 and cant_val > 0:
                services.carrito_libre_agregar(
                    request.session, 
                    nombre=nombre[:100], 
                    precio=p_val, 
                    costo=c_val, 
                    cantidad=cant_val
                )
                messages.success(request, f'Producto libre "{nombre}" agregado por ${p_val}.')
            else:
                messages.error(request, 'Revisa los datos: nombre requerido, precio/costo >= 0 y cantidad > 0.')
        except ValueError:
            messages.error(request, 'Asegúrate de ingresar números válidos en precio, costo y cantidad.')
            
    return redirect('nueva_venta')


@tienda_requerida
def carrito_libre_quitar_view(request, id_libre):
    """Quita un producto libre del carrito."""
    services.carrito_libre_quitar(request.session, id_libre)
    return redirect('nueva_venta')


# ── Ventas ─────────────────────────────────────────────────────────────────

@tienda_requerida
def lista_ventas(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
    ventas = services.get_ventas(negocio.slug)

    # Filtros
    fecha  = request.GET.get('fecha', '')
    metodo = request.GET.get('metodo', '')
    tipo   = request.GET.get('tipo', '')

    if fecha:
        ventas = ventas.filter(fecha=fecha)
    if metodo:
        ventas = ventas.filter(metodo_pago=metodo)
    if tipo:
        ventas = ventas.filter(tipo=tipo)

    return render(request, 'ventas/lista.html', {
        'negocio':       negocio,
        'negocios':      negocios,
        'ventas':        ventas,
        'filtro_fecha':  fecha,
        'filtro_metodo': metodo,
        'filtro_tipo':   tipo,
        'carrito_count': len(services.get_carrito(request.session)),
    })


@tienda_requerida
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
        observacion = request.POST.get('observacion', '').strip()[:500]

        venta = services.crear_venta(
            negocio=negocio,
            fecha=fecha,
            tipo=tipo,
            metodo_pago=metodo_pago,
            items_data=carrito_items,
            observacion=observacion,
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


@tienda_requerida
def ventas_bulk_eliminar(request):
    """Elimina las ventas seleccionadas y restaura el stock asociado."""
    if request.method == 'POST':
        negocio, _ = _contexto_base(request)
        if not negocio:
            return redirect('lista_productos')
            
        venta_ids = request.POST.getlist('venta_ids')
        if not venta_ids:
            messages.warning(request, 'No seleccionaste ninguna venta para eliminar.')
            return redirect('lista_ventas')
            
        try:
            ids_enteros = [int(vid) for vid in venta_ids]
            count = services.eliminar_ventas(ids_enteros)
            if count > 0:
                messages.success(request, f'Se eliminaron {count} venta(s) exitosamente.')
            else:
                messages.warning(request, 'Las ventas indicadas no existen o ya fueron eliminadas.')
        except ValueError:
            messages.error(request, 'Error al procesar la solicitud.')
            
    return redirect('lista_ventas')


@tienda_requerida
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

@tienda_requerida
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


@tienda_requerida
def crear_insumo(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('calculadora_costos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        costo_unitario = request.POST.get('costo_unitario', '0')
        if nombre and costo_unitario:
            try:
                c_val = float(costo_unitario)
                if c_val < 0:
                    messages.error(request, 'El costo no puede ser negativo.')
                else:
                    services.crear_insumo(
                        negocio=negocio,
                        nombre=nombre[:100],
                        costo_unitario=c_val
                    )
                    messages.success(request, f'Insumo "{nombre}" creado exitosamente.')
                    return redirect('calculadora_costos')
            except ValueError:
                messages.error(request, 'Costo unitario inválido.')
        else:
            messages.error(request, 'El nombre y el costo son obligatorios.')

    return render(request, 'calculadora/form_insumo.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo insumo',
        'insumo': None,
        'carrito_count': len(services.get_carrito(request.session)),
    })


@tienda_requerida
def editar_insumo(request, pk):
    negocio, negocios = _contexto_base(request)
    insumo = get_object_or_404(services.Insumo, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        costo_unitario = request.POST.get('costo_unitario', '0')
        if nombre and costo_unitario:
            try:
                c_val = float(costo_unitario)
                if c_val < 0:
                    messages.error(request, 'El costo no puede ser negativo.')
                else:
                    services.actualizar_insumo(
                        pk=pk,
                        nombre=nombre[:100],
                        costo_unitario=c_val
                    )
                    messages.success(request, f'Insumo "{nombre}" actualizado.')
                    return redirect('calculadora_costos')
            except ValueError:
                messages.error(request, 'Costo unitario inválido.')
        else:
            messages.error(request, 'El nombre y el costo son obligatorios.')

    return render(request, 'calculadora/form_insumo.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar insumo',
        'insumo': insumo,
        'carrito_count': len(services.get_carrito(request.session)),
    })


@tienda_requerida
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
    # Solo mostrar productos con stock disponible
    productos = services.get_productos(slug).filter(stock__gt=0)
    
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    if query:
        productos = productos.filter(nombre__icontains=query)
    if tipo:
        productos = productos.filter(tipo=tipo)

    tipos = negocio.categorias_producto.all()

    carrito_items = services.get_carrito_publico_detalle(request.session, slug)
    carrito_count = sum(item['cantidad'] for item in carrito_items)
    top_vendidos = services.get_top_vendidos(slug)

    # Anotar cada producto con la cantidad ya en el carrito del cliente
    carrito_cantidades = {item['producto'].pk: item['cantidad'] for item in carrito_items}
    productos_con_cant = [
        (p, carrito_cantidades.get(p.pk, 0))
        for p in productos
    ]

    return render(request, 'tienda_publica/index.html', {
        'negocio': negocio,
        'productos_con_cant': productos_con_cant,
        'query': query,
        'tipo_activo': tipo,
        'tipos': tipos,
        'carrito_count': carrito_count,
        'top_vendidos': top_vendidos,
    })

def agregar_carrito_publico(request, slug, pk):
    producto = get_object_or_404(services.Producto, pk=pk, negocio__slug=slug)
    carrito = request.session.get('carrito_publico', {})
    cantidad_actual = carrito.get(str(pk), 0)
    if cantidad_actual >= producto.stock:
        messages.warning(request, f'Solo hay {producto.stock} unidad(es) disponible(s) de "{producto.nombre}".')
    else:
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
        nombre = request.POST.get('nombre', '').strip()[:100]
        telefono = request.POST.get('telefono', '').strip()[:30]
        direccion = request.POST.get('direccion', '').strip()[:255]
        
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

@tienda_requerida
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

@tienda_requerida
def aceptar_pedido(request, pk):
    _negocio, _negocios = _contexto_base(request)
    if request.method == 'POST':
        if services.aceptar_pedido(pk):
            messages.success(request, 'Pedido aceptado y convertido en venta.')
        else:
            messages.error(request, 'No se pudo aceptar el pedido (tal vez ya no está pendiente).')
    return redirect('lista_pedidos')

@tienda_requerida
def eliminar_pedido(request, pk):
    _negocio, _negocios = _contexto_base(request)
    if request.method == 'POST':
        if services.eliminar_pedido(pk):
            messages.success(request, 'Pedido eliminado/rechazado.')
        else:
            messages.error(request, 'No se encontró el pedido.')
    return redirect('lista_pedidos')

# ── Notas ──────────────────────────────────────────────────────────────────

@tienda_requerida
def lista_notas(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
        
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()[:1000]
        if texto:
            Nota.objects.create(negocio=negocio, texto=texto)
            messages.success(request, 'Nota agregada exitosamente.')
        return redirect('lista_notas')
    notas = Nota.objects.filter(negocio=negocio)
    return render(request, 'notas/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'notas': notas,
        'carrito_count': len(services.get_carrito(request.session)),
    })

@tienda_requerida
def eliminar_nota(request, pk):
    negocio, _ = _contexto_base(request)
    nota = get_object_or_404(Nota, pk=pk, negocio=negocio)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota eliminada.')
    return redirect('lista_notas')


@tienda_requerida
def cambiar_tipo_venta(request, pk):
    """Permite cambiar el tipo de venta (pagada/credito) vía AJAX."""
    if request.method == 'POST':
        negocio, _ = _contexto_base(request)
        if negocio is None:
            return JsonResponse({'error': 'No autorizado'}, status=403)
            
        try:
            data = json.loads(request.body)
            nuevo_tipo = data.get('tipo')
            venta = get_object_or_404(services.Venta, pk=pk, negocio=negocio)
            
            # TIPO_CHOICES de Venta: [('pagada', 'Pagada'), ('credito', 'A crédito')]
            if nuevo_tipo in ['pagada', 'credito']:
                venta.tipo = nuevo_tipo
                venta.save()
                # Retornamos display para actualizar el DOM fácilmente si hiciera falta
                display = 'Pagada' if nuevo_tipo == 'pagada' else 'A crédito'
                return JsonResponse({'status': 'success', 'nuevo_tipo': venta.tipo, 'display': display})
            else:
                return JsonResponse({'error': 'Tipo inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ── Autenticación y Cuentas ───────────────────────────────────────────────

def user_login(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Hola de nuevo, {user.username}!')
            return redirect('inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
        
    return render(request, 'auth/login.html', {'form': form})

def user_register(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada con éxito! Vamos a configurar tu tienda.')
            return redirect('crear_tienda_inicial')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserCreationForm()
        
    return render(request, 'auth/registro.html', {'form': form})

from django.contrib.auth.decorators import login_required

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Sesión terminada.')
    return redirect('login')

@login_required
def crear_tienda_inicial(request):
    """Vista de onboarding obligatorio si el usuario no tiene tiendas."""
    if request.user.negocios.exists():
        return redirect('inicio')
        
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()[:100]
        if nombre:
            import re
            slug = re.sub(r'[^a-z0-9]', '', nombre.lower())
            base_slug = slug
            counter = 1
            while Negocio.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            negocio = Negocio.objects.create(
                nombre=nombre,
                slug=slug,
                propietario=request.user,
                color_primario='#ec4899',
                color_secundario='#be185d'
            )
            # Add default categories
            for t_code, t_name in [('accesorios', 'Accesorios'), ('papeleria', 'Papelería'), ('bazar', 'Bazar')]:
                CategoriaProducto.objects.create(negocio=negocio, nombre=t_name)
                
            messages.success(request, f'¡Tu tienda "{nombre}" fue creada correctamente!')
            # Set default session
            request.session['negocio_slug'] = negocio.slug
            return redirect('inicio')
        else:
            messages.error(request, 'Debes ingresar un nombre para tu tienda.')
            
    return render(request, 'auth/crear_tienda.html')


# ── Configuración ─────────────────────────────────────────────────────────

@tienda_requerida
def configuracion_tienda(request):
    negocio, negocios = _contexto_base(request)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()[:100]
        descripcion = request.POST.get('descripcion', '').strip()[:500]
        emoji = request.POST.get('emoji', '🛍️').strip()[:10]
        if nombre:
            negocio.nombre = nombre
            negocio.descripcion = descripcion
            negocio.emoji = emoji
            negocio.save()
            messages.success(request, 'Información de la tienda actualizada.')
            return redirect('configuracion_tienda')
        else:
            messages.error(request, 'El nombre no puede estar vacío.')
            
    return render(request, 'config/tienda.html', {
        'negocio': negocio,
        'negocios': negocios,
    })

@tienda_requerida
def configuracion_categorias(request):
    negocio, negocios = _contexto_base(request)
    categorias = negocio.categorias_producto.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            nombre = request.POST.get('nombre', '').strip()[:50]
            if nombre:
                CategoriaProducto.objects.get_or_create(negocio=negocio, nombre=nombre)
                messages.success(request, f'Categoría "{nombre}" agregada.')
            else:
                messages.error(request, 'Ingresa un nombre válido.')
        elif action == 'delete':
            cat_id = request.POST.get('categoria_id')
            try:
                cat = CategoriaProducto.objects.get(pk=cat_id, negocio=negocio)
                cat.delete()
                messages.success(request, 'Categoría eliminada.')
            except CategoriaProducto.DoesNotExist:
                messages.error(request, 'Error al borrar la categoría (o no existe).')
        return redirect('configuracion_categorias')

    return render(request, 'config/categorias.html', {
        'negocio': negocio,
        'negocios': negocios,
        'categorias': categorias,
    })

@tienda_requerida
def configuracion_usuarios(request):
    negocio, negocios = _contexto_base(request)
    users_list = []
    
    if request.user.is_superuser:
        users_list = User.objects.all().prefetch_related('negocios')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. El propio usuario cambia sus datos
        if action == 'update_self':
            new_username = request.POST.get('username', '').strip()[:150]
            new_email = request.POST.get('email', '').strip()[:254]
            
            if new_username:
                if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'Este nombre de usuario ya está en uso.')
                else:
                    request.user.username = new_username
                    request.user.email = new_email
                    request.user.save()
                    messages.success(request, '¡Tus datos han sido actualizados!')
            else:
                messages.error(request, 'El nombre de usuario no puede estar vacío.')
            return redirect('configuracion_usuarios')

        # 2. El superusuario cambia datos o clave de otros
        if request.user.is_superuser:
            user_id = request.POST.get('user_id')
            try:
                target_user = User.objects.get(pk=user_id)
                
                if action == 'change_password':
                    new_pass = request.POST.get('new_password', '').strip()
                    if new_pass:
                        target_user.set_password(new_pass)
                        target_user.save()
                        messages.success(request, f'¡Contraseña actualizada para @{target_user.username}!')
                    else:
                        messages.error(request, 'La clave no puede estar vacía.')
                        
                elif action == 'admin_update_profile':
                    adm_username = request.POST.get('username', '').strip()[:150]
                    adm_email = request.POST.get('email', '').strip()[:254]
                    if adm_username:
                        if User.objects.filter(username=adm_username).exclude(pk=target_user.pk).exists():
                            messages.error(request, f'El nombre @{adm_username} ya está en uso por otra cuenta.')
                        else:
                            target_user.username = adm_username
                            target_user.email = adm_email
                            target_user.save()
                            messages.success(request, f'Perfil de @{target_user.username} actualizado correctamente.')
                    else:
                        messages.error(request, 'El nombre de usuario no puede estar vacío.')
                        
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
            return redirect('configuracion_usuarios')
    
    return render(request, 'config/usuarios.html', {
        'negocio': negocio,
        'negocios': negocios,
        'users_list': users_list,
    })
