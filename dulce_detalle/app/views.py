from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
    return render(request, 'productos/lista.html', {
        'negocio': negocio,
        'negocios': negocios,
        'productos': productos,
    })


def crear_producto(request):
    negocio, negocios = _contexto_base(request)
    if negocio is None:
        return redirect('lista_productos')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        descripcion = request.POST.get('descripcion', '').strip()
        stock = request.POST.get('stock', '0')
        if nombre and precio:
            try:
                services.crear_producto(
                    negocio=negocio,
                    nombre=nombre,
                    precio=float(precio),
                    descripcion=descripcion,
                    stock=int(stock),
                )
                messages.success(request, f'Producto "{nombre}" creado exitosamente.')
                return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Precio o stock inválidos.')
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
        descripcion = request.POST.get('descripcion', '').strip()
        stock = request.POST.get('stock', '0')
        if nombre and precio:
            try:
                services.actualizar_producto(
                    pk=pk,
                    nombre=nombre,
                    precio=float(precio),
                    descripcion=descripcion,
                    stock=int(stock),
                )
                messages.success(request, f'Producto "{nombre}" actualizado.')
                return redirect('lista_productos')
            except ValueError:
                messages.error(request, 'Precio o stock inválidos.')
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