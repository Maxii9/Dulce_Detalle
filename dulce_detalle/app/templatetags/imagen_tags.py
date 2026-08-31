"""
Template tags para optimización de imágenes Cloudinary.

Uso en templates:
    {% load imagen_tags %}
    <img src="{% cloudinary_thumb producto.imagen 400 400 %}" loading="lazy" ...>

El tag detecta si la URL es de Cloudinary y aplica transformaciones automáticas:
    - w_ / h_: redimensiona al tamaño indicado
    - c_fill: recorte inteligente para mantener proporción
    - q_auto: calidad automática optimizada por Cloudinary
    - f_auto: formato automático (WebP en navegadores que lo soportan)

Si la imagen NO es de Cloudinary (filesystem local), devuelve la URL sin modificar.
"""
from django import template
import re

register = template.Library()


def _build_cloudinary_thumb_url(url: str, width: int, height: int) -> str:
    """
    Inserta transformaciones Cloudinary en una URL de imagen.

    Cloudinary URLs tienen la forma:
        https://res.cloudinary.com/<cloud>/image/upload/<transformaciones>/<version>/<public_id>
    
    Si ya hay transformaciones, las reemplazamos. Si no, las insertamos después de /upload/.
    """
    if not url or 'res.cloudinary.com' not in url:
        return url  # URL local (filesystem), no tocar

    transform = f"w_{width},h_{height},c_fill,q_auto,f_auto"

    # Patrón: .../upload/[transformaciones_existentes]/<resto>
    # Queremos reemplazar o insertar justo después de /upload/
    pattern = r'(/upload/)(?:[^/]+/)*'
    
    # Verificar si ya tiene transformaciones (contiene letras seguidas de _ y números)
    upload_idx = url.find('/upload/')
    if upload_idx == -1:
        return url

    after_upload = url[upload_idx + len('/upload/'):]
    
    # Detectar si lo que sigue es una transformación (ej: w_800,h_600,...) o directamente el contenido
    # Las transformaciones empiezan con una letra seguida de _ (ej: w_, h_, c_, q_, f_, v12345...)
    # Los version tokens empiezan con 'v' seguido de dígitos
    has_transform = bool(re.match(r'^[a-z]+_', after_upload))
    has_version = bool(re.match(r'^v\d+/', after_upload))
    
    base = url[:upload_idx + len('/upload/')]

    if has_transform:
        # Reemplazar las transformaciones existentes
        # Encontrar el fin de la sección de transformaciones (hasta el primer / que no sea parte de una transform)
        rest = after_upload
        # Las transformaciones son segmentos separados por / que contienen _
        segments = rest.split('/')
        # Saltar segmentos que son transformaciones (contienen _) o versiones (v + dígitos)
        skip = 0
        for seg in segments:
            if re.match(r'^[a-z]+_', seg) or re.match(r'^v\d+$', seg):
                skip += 1
            else:
                break
        remainder = '/'.join(segments[skip:])
        return f"{base}{transform}/{remainder}"
    elif has_version:
        # Tiene versión pero no transformaciones: insertar antes de la versión
        return f"{base}{transform}/{after_upload}"
    else:
        # No tiene ni transformaciones ni versión
        return f"{base}{transform}/{after_upload}"


@register.simple_tag
def cloudinary_thumb(image_field, width=400, height=400):
    """
    Devuelve una URL de Cloudinary con transformaciones de tamaño aplicadas.
    Si la imagen no existe o no es de Cloudinary, devuelve ''.

    Ejemplo de uso:
        {% cloudinary_thumb producto.imagen 400 400 %}
    """
    if not image_field:
        return ''
    try:
        url = image_field.url
    except Exception:
        return ''
    return _build_cloudinary_thumb_url(url, width, height)
