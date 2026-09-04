"""Context processors that inject variables into every template context."""
from django.db.models import Q, Exists, OuterRef


def carrito_info(request):
    """Inyecta el conteo del carrito en todos los templates."""
    carrito = request.session.get('carrito', {})
    return {
        'carrito_count': len(carrito),
        'current_view': request.resolver_match.url_name if request.resolver_match else '',
    }


def notificaciones_info(request):
    """Inyecta las notificaciones no descartadas del usuario en todos los templates."""
    if not request.user.is_authenticated:
        return {}
    try:
        from app.models import Notificacion, Negocio

        # Tiendas que administra este usuario
        negocios_usuario = Negocio.objects.filter(propietario=request.user)

        # Tabla intermedia del ManyToMany Notificacion <-> Negocio
        Through = Notificacion.destinatarios.through

        # Subquery: "esta notificación tiene ALGÚN destinatario (no es broadcast)"
        tiene_cualquier_dest = Through.objects.filter(notificacion=OuterRef('pk'))

        # Subquery: "esta notificación incluye alguna tienda del usuario"
        me_incluye = Through.objects.filter(
            notificacion=OuterRef('pk'),
            negocio__in=negocios_usuario,
        )

        # Mostrar si es broadcast (sin ningún destinatario) O si me incluye
        notifs = (
            Notificacion.objects
            .filter(
                Q(~Exists(tiene_cualquier_dest)) |  # broadcast global
                Q(Exists(me_incluye))               # dirigida a mis tiendas
            )
            .exclude(descartada_por=request.user)
            .distinct()
            .order_by('-creado')[:20]
        )
        count = notifs.count()
        return {
            'notificaciones':       notifs,
            'notificaciones_count': count,
        }
    except Exception:
        return {}
