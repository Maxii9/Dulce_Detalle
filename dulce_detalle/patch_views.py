import re

with open('app/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# PATCH lista_productos
patch_lista_1 = r"""
    from .models import Producto as ProdModel
    tipos = ProdModel.TIPO_CHOICES
"""
replace_lista_1 = r"""
    tipos = negocio.categorias_producto.all()
"""
content = content.replace(patch_lista_1, replace_lista_1)

# PATCH crear_producto
patch_crear = r"""
    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo producto',
        'producto': None,
    })
"""
replace_crear = r"""
    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Nuevo producto',
        'producto': None,
        'categorias': negocio.categorias_producto.all(),
    })
"""
content = content.replace(patch_crear, replace_crear)

# PATCH editar_producto
patch_editar = r"""
    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar producto',
        'producto': producto,
    })
"""
replace_editar = r"""
    return render(request, 'productos/form.html', {
        'negocio': negocio,
        'negocios': negocios,
        'accion': 'Editar producto',
        'producto': producto,
        'categorias': negocio.categorias_producto.all(),
    })
"""
content = content.replace(patch_editar, replace_editar)

with open('app/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Vistas parcheadas con 'categorias'.")
