import codecs

new_views = """

# ── Autenticación y Cuentas ───────────────────────────────────────────────

def user_login(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Hola de nuevo, {user.username}!')
            return redirect('inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
        
    return render(request, 'auth/login.html', {'form': form})

def user_register(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Cuenta creada con éxito! Vamos a configurar tu tienda.')
            return redirect('crear_tienda_inicial')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = UserCreationForm()
        
    return render(request, 'auth/registro.html', {'form': form})

from django.contrib.auth.decorators import login_required

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Sesión terminada.')
    return redirect('login')

@login_required
def crear_tienda_inicial(request):
    \"\"\"Vista de onboarding obligatorio si el usuario no tiene tiendas.\"\"\"
    if request.user.negocios.exists():
        return redirect('inicio')
        
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if nombre:
            import re
            slug = re.sub(r'[^a-z0-9]', '', nombre.lower())
            base_slug = slug
            counter = 1
            while settings.apps.get_model('app', 'Negocio').objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            negocio = settings.apps.get_model('app', 'Negocio').objects.create(
                nombre=nombre,
                slug=slug,
                propietario=request.user,
                color_primario='#ec4899',
                color_secundario='#be185d'
            )
            # Add default categories
            for t_code, t_name in [('accesorios', 'Accesorios'), ('papeleria', 'Papelería'), ('bazar', 'Bazar')]:
                CategoriaProducto.objects.create(negocio=negocio, nombre=t_name)
                
            messages.success(request, f'¡Tu tienda "{nombre}" fue creada correctamente!')
            # Set default session
            request.session['negocio_slug'] = negocio.slug
            return redirect('inicio')
        else:
            messages.error(request, 'Debes ingresar un nombre para tu tienda.')
            
    return render(request, 'auth/crear_tienda.html')


# ── Configuración ─────────────────────────────────────────────────────────

@tienda_requerida
def configuracion_tienda(request):
    negocio, negocios = _contexto_base(request)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        emoji = request.POST.get('emoji', '🛍️')
        if nombre:
            negocio.nombre = nombre
            negocio.descripcion = descripcion
            negocio.emoji = emoji
            negocio.save()
            messages.success(request, 'Información de la tienda actualizada.')
            return redirect('configuracion_tienda')
        else:
            messages.error(request, 'El nombre no puede estar vacío.')
            
    return render(request, 'config/tienda.html', {
        'negocio': negocio,
        'negocios': negocios,
    })

@tienda_requerida
def configuracion_categorias(request):
    negocio, negocios = _contexto_base(request)
    categorias = negocio.categorias_producto.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            nombre = request.POST.get('nombre', '').strip()
            if nombre:
                CategoriaProducto.objects.get_or_create(negocio=negocio, nombre=nombre)
                messages.success(request, f'Categoría "{nombre}" agregada.')
            else:
                messages.error(request, 'Ingresa un nombre válido.')
        elif action == 'delete':
            cat_id = request.POST.get('categoria_id')
            try:
                cat = CategoriaProducto.objects.get(pk=cat_id, negocio=negocio)
                cat.delete()
                messages.success(request, 'Categoría eliminada.')
            except CategoriaProducto.DoesNotExist:
                messages.error(request, 'Error al borrar la categoría (o no existe).')
        return redirect('configuracion_categorias')

    return render(request, 'config/categorias.html', {
        'negocio': negocio,
        'negocios': negocios,
        'categorias': categorias,
    })

@tienda_requerida
def configuracion_usuarios(request):
    negocio, negocios = _contexto_base(request)
    # Por ahora solo listamos el propietario
    return render(request, 'config/usuarios.html', {
        'negocio': negocio,
        'negocios': negocios,
    })
"""

with codecs.open('app/views.py', 'a', encoding='utf-8') as f:
    f.write(new_views)

# Adding imports at start
with codecs.open('app/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from django.apps import apps", "from django.apps import apps\nfrom django.conf import settings")

with codecs.open('app/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Vistas de auth y configuración añadidas correctamente.")
