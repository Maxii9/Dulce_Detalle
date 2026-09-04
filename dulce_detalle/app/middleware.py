"""
Middleware personalizado para manejar errores CSRF de forma amigable.

En lugar de mostrar la página genérica 403 del navegador, redirige al usuario
a la misma página via GET para que pueda volver a intentar la acción.
"""

from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import redirect
from django.contrib import messages


class CsrfAmiableMiddleware(CsrfViewMiddleware):
    """
    Extiende el middleware CSRF estándar de Django para manejar fallos
    de verificación de forma más amigable con el usuario.

    Cuando un token CSRF es inválido (expirado, botón "atrás", etc.),
    en lugar de mostrar el error 403, redirige al usuario a la misma URL
    via GET con un mensaje explicativo.
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Llamar al proceso CSRF estándar
        result = super().process_view(request, callback, callback_args, callback_kwargs)

        # Si retornó una respuesta (significa que falló la verificación CSRF)
        if result is not None and result.status_code == 403:
            # Agregar mensaje de aviso amigable
            messages.warning(
                request,
                'Tu sesión venció o la página expiró. Por favor, intentalo de nuevo.'
            )
            # Redirigir a la misma URL pero como GET (evita re-envío del form)
            return redirect(request.path)

        return result
