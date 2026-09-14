"""
Template tags de apoyo para paginación.

Uso en templates:
    {% load paginacion_tags %}
    <a href="?{% url_replace page=2 %}">...</a>

`url_replace` reutiliza la querystring actual y reemplaza/añade el parámetro
indicado (por defecto `page`), preservando filtros activos como q, categoria,
fecha, metodo, etc.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    request = context.get('request')
    if request is None:
        return ''
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            params[key] = value
        else:
            params.pop(key, None)
    return params.urlencode()