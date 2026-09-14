"""Context processors that inject variables into every template context."""
from django.db.models import Q, Exists, OuterRef
from django.core.cache import cache

# Segundos durante los cuales se reutiliza la consulta de notificaciones por usuario.
_NOTIFICACIONES_TTL = 60


def carrito_info(request):
    """Inyecta el conteo del carrito en todos los templates."""
    carrito = request.session.get('carrito', {})
    return {
        'carrito_count': len(carrito),
        'current_view': request.resolver_match.url_name if request.resolver_match else '',
    }


def notificaciones_info(request):
    """Inyecta las notificaciones no descartadas del usuario en todos los templates.

    El resultado se cachea brevemente por usuario para no consultar la base en
    cada render (el dropdown aparece en todas las páginas autenticadas).
    """
    if not request.user.is_authenticated:
        return {}
    cache_key = f'notificaciones:{request.user.pk}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
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
        data = {
            'notificaciones':       list(notifs),
            'notificaciones_count': count,
        }
        cache.set(cache_key, data, _NOTIFICACIONES_TTL)
        return data
    except Exception:
        return {}
