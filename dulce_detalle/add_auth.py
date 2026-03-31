import re
import os

with open('app/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

funcs_to_protect = [
    'inicio', 'cambiar_negocio', 'lista_productos', 'crear_producto',
    'editar_producto', 'eliminar_producto', 'carrito_agregar', 'carrito_quitar',
    'carrito_limpiar', 'carrito_libre_agregar_view', 'carrito_libre_quitar_view',
    'lista_ventas', 'nueva_venta', 'ventas_bulk_eliminar', 'cambiar_tipo_venta',
    'estadisticas_ventas', 'calculadora_costos', 'crear_insumo', 'editar_insumo',
    'eliminar_insumo', 'lista_pedidos', 'aceptar_pedido', 'eliminar_pedido',
    'lista_notas', 'eliminar_nota'
]

decorator_code = """
import functools
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from app.models import Negocio, CategoriaProducto

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

# Modificando _contexto_base original
"""

new_context = """
def _contexto_base(request):
    \"\"\"Contexto compartido con datos del negocio activo para el usuario.\"\"\"
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
"""

if "def tienda_requerida" not in content:
    content = content.replace("from app import services", "from app import services\n" + decorator_code)

if "def _contexto_base(request):" in content and "request.user.is_authenticated" not in content:
    content = re.sub(r'def _contexto_base\(request\):[\s\S]*?return negocio, negocios', new_context.strip(), content)

for func in funcs_to_protect:
    pattern = r'(def ' + func + r'\()'
    replacement = r'@tienda_requerida\n\1'
    if f"@tienda_requerida\ndef {func}(" not in content:
        content = re.sub(pattern, replacement, content)

with open('app/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Vistas protegidas agregando @tienda_requerida.")
