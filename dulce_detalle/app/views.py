from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json
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
        
    carrito_items = services.get_carrito_detalle(request.session)
    total = services.carrito_total(request.session)
    
    valor_inventario = sum(p.costo * p.stock for p in productos)
        
    return render(request, 'productos/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'productos': productos,
        'query': query,
        'carrito_items': carrito_items,
        'total': total,
        'carrito_count': len(carrito_items),
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
    """Quita un producto del carrito y vuelve a la página anterior."""
    services.carrito_quitar(request.session, pk)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
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
        observacion = request.POST.get('observacion', '').strip()

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


# ── Notas ──────────────────────────────────────────────────────────────────

def lista_notas(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')
        
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        if texto:
            from .models import Nota
            Nota.objects.create(negocio=negocio, texto=texto)
            messages.success(request, 'Nota agregada exitosamente.')
        return redirect('lista_notas')
        
    from .models import Nota
    notas = Nota.objects.filter(negocio=negocio)
    return render(request, 'notas/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'notas': notas,
        'carrito_count': len(services.get_carrito(request.session)),
    })

def eliminar_nota(request, pk):
    negocio, _ = _contexto_base(request)
    from .models import Nota
    nota = get_object_or_404(Nota, pk=pk, negocio=negocio)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota eliminada.')
    return redirect('lista_notas')


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