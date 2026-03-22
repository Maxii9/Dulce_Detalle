"""Context processors that inject variables into every template context."""


def carrito_info(request):
    """Inyecta el conteo del carrito en todos los templates."""
    carrito = request.session.get('carrito', {})
    return {
        'carrito_count': len(carrito),
        'current_view': request.resolver_match.url_name if request.resolver_match else '',
    }
