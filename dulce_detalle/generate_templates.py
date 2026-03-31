import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

# LOGIN
login_html = """
{% extends 'base.html' %}
{% block title %}Iniciar Sesión{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-16 bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
  <div class="text-center mb-8">
    <span class="text-4xl">🛍️</span>
    <h1 class="text-2xl font-bold text-gray-900 mt-4">Iniciar Sesión</h1>
    <p class="text-gray-500 text-sm mt-1">Ingresa para administrar tus tiendas</p>
  </div>
  <form method="post" class="space-y-4">
    {% csrf_token %}
    {% for field in form %}
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}
          <p class="text-red-500 text-xs mt-1">{{ field.errors.0 }}</p>
        {% endif %}
      </div>
    {% endfor %}
    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow mt-4">Entrar a mi cuenta</button>
  </form>
  <p class="text-center text-sm text-gray-500 mt-6">¿No tienes cuenta? <a href="{% url 'registro' %}" class="text-emerald-600 font-bold hover:underline">Regístrate aquí</a></p>
</div>
<style>
  form input { border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 0.6rem 0.8rem; width: 100%; font-size: 0.875rem;}
  form input:focus { outline: none; border-color: #059669; box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2); }
</style>
{% endblock %}
"""

# REGISTRO
registro_html = """
{% extends 'base.html' %}
{% block title %}Crear una cuenta{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-16 bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
  <div class="text-center mb-8">
    <span class="text-4xl">👋</span>
    <h1 class="text-2xl font-bold text-gray-900 mt-4">Crear una cuenta</h1>
    <p class="text-gray-500 text-sm mt-1">Unete gratis y gestiona tu inventario y ventas</p>
  </div>
  <form method="post" class="space-y-4">
    {% csrf_token %}
    {% for field in form %}
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}
          <p class="text-red-500 text-xs mt-1">{{ field.errors.0 }}</p>
        {% endif %}
      </div>
    {% endfor %}
    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow mt-4">Crear mi cuenta</button>
  </form>
  <p class="text-center text-sm text-gray-500 mt-6">¿Ya tienes cuenta? <a href="{% url 'login' %}" class="text-emerald-600 font-bold hover:underline">Inicia sesión</a></p>
</div>
<style>
  form input { border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 0.6rem 0.8rem; width: 100%; font-size: 0.875rem;}
  form input:focus { outline: none; border-color: #059669; box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.2); }
  form .helptext { font-size: 0.7rem; color: #6b7280; display:block; margin-top:2px; }
  form ul { display:none; }
</style>
{% endblock %}
"""

# CREAR TIENDA
tienda_html = """
{% extends 'base.html' %}
{% block title %}Crea tu primera tienda{% endblock %}
{% block content %}
<div class="max-w-xl mx-auto mt-16 bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
  <div class="text-center mb-8">
    <span class="text-5xl">🏪</span>
    <h1 class="text-3xl font-bold text-gray-900 mt-4">Bienvenido, {{ request.user.username }}</h1>
    <p class="text-gray-500 text-sm mt-2">Para empezar a usar el sistema, debes crear tu primera tienda. ¡Sólo te tomará un segundo!</p>
  </div>
  <form method="post" class="space-y-6">
    {% csrf_token %}
    <div>
      <label class="block text-sm font-bold text-gray-700 mb-2">Nombre de tu tienda (ej: MangoAccesorios) <span class="text-red-500">*</span></label>
      <input type="text" name="nombre" required placeholder="Ingresa el nombre de tu marca" class="w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500">
      <p class="text-xs text-gray-500 mt-2">No te preocupes, luego podrás personalizar el color y el emoji desde la Configuración.</p>
    </div>
    
    <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-4 rounded-xl transition-all shadow-lg text-lg">
      ¡Crear Tienda y Comenzar!
    </button>
  </form>
</div>
{% endblock %}
"""

# CONFIGURAR TIENDA
config_tienda = """
{% extends 'base.html' %}
{% block title %}Configuración de la Tienda{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto">
  <h1 class="text-2xl font-bold text-content-title mb-6 flex items-center gap-2">
    <span>⚙️</span> Información del Negocio
  </h1>
  <div class="bg-card-bg rounded-2xl shadow-sm border border-card-border p-6">
    <form method="post" class="space-y-5">
      {% csrf_token %}
      <div>
        <label class="block text-sm font-bold text-content-subtitle mb-2">Nombre público <span class="text-red-500">*</span></label>
        <input type="text" name="nombre" value="{{ negocio.nombre }}" required class="w-full border border-input-border rounded-lg px-4 py-2 text-input-text focus:outline-none focus:ring-2 focus:ring-input-focus">
      </div>
      <div>
        <label class="block text-sm font-bold text-content-subtitle mb-2">Emoji de la tienda</label>
        <input type="text" name="emoji" value="{{ negocio.emoji }}" class="w-full sm:w-20 text-2xl border border-input-border rounded-lg px-4 py-2 text-input-text focus:outline-none focus:ring-2 focus:ring-input-focus text-center">
      </div>
      <div>
        <label class="block text-sm font-bold text-content-subtitle mb-2">Descripción (Opcional)</label>
        <textarea name="descripcion" rows="3" class="w-full border border-input-border rounded-lg px-4 py-2 text-input-text focus:outline-none focus:ring-2 focus:ring-input-focus">{{ negocio.descripcion }}</textarea>
      </div>
      <button type="submit" class="mt-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-6 rounded-lg transition-colors">Guardar Cambios</button>
    </form>
  </div>
</div>
{% endblock %}
"""

# CONFIGURAR CATEGORIAS
config_cat = """
{% extends 'base.html' %}
{% block title %}Tipos de Producto{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto">
  <h1 class="text-2xl font-bold text-content-title mb-6 flex items-center gap-2">
    <span>🗂️</span> Tipos de Producto
  </h1>
  <p class="text-content-subtitle text-sm mb-6">Estas son las opciones que aparecerán en el menú desplegable de "Tipo" a la hora de crear un nuevo producto.</p>
  
  <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
    
    <!-- Agregar categoria -->
    <div class="bg-card-bg rounded-2xl shadow-sm border border-card-border p-6 h-fit">
      <h3 class="font-bold text-content-title mb-4">Añadir nuevo tipo</h3>
      <form method="post" class="flex flex-col gap-3">
        {% csrf_token %}
        <input type="hidden" name="action" value="add">
        <input type="text" name="nombre" placeholder="Ej: Pijamas" required class="w-full border border-input-border rounded-lg px-4 py-2 text-input-text focus:outline-none focus:ring-2 focus:ring-input-focus">
        <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-lg transition-colors w-full">+ Guardar Tipo</button>
      </form>
    </div>

    <!-- Listado -->
    <div class="bg-card-bg rounded-2xl shadow-sm border border-card-border overflow-hidden">
      {% if categorias %}
      <ul class="divide-y divide-card-border">
        {% for cat in categorias %}
        <li class="p-4 flex justify-between items-center hover:bg-card-row-hover transition-colors">
          <span class="font-semibold text-content-value">{{ cat.nombre }}</span>
          <form method="post" onsubmit="return confirm('¿Seguro quieres borrar esto? Los productos preexistentes mantendrán el nombre de The tipo en texto plano, pero ya no aparecerá como opción para nuevos productos.')">
            {% csrf_token %}
            <input type="hidden" name="action" value="delete">
            <input type="hidden" name="categoria_id" value="{{ cat.id }}">
            <button type="submit" class="text-red-500 hover:text-red-700 text-sm font-bold bg-red-50 px-2 py-1 rounded">Eliminar</button>
          </form>
        </li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="p-6 text-center text-content-muted">
        No hay categorías creadas.
      </div>
      {% endif %}
    </div>

  </div>
</div>
{% endblock %}
"""

# CONFIGURAR USUARIOS
config_usu = """
{% extends 'base.html' %}
{% block title %}Usuarios del Equipo{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto">
  <h1 class="text-2xl font-bold text-content-title mb-6 flex items-center gap-2">
    <span>👥</span> Mi Cuenta y Equipo
  </h1>
  <div class="bg-card-bg rounded-2xl shadow-sm border border-card-border p-6">
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center text-2xl font-bold text-purple-600">
        {{ request.user.username|make_list|first|upper }}
      </div>
      <div>
        <h3 class="font-bold text-lg text-content-value">{{ request.user.username }}</h3>
        <p class="text-content-subtitle">{{ request.user.email }}</p>
        <span class="inline-block mt-2 px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded">Propietario / Administrador</span>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

create_file('app/templates/auth/login.html', login_html)
create_file('app/templates/auth/registro.html', registro_html)
create_file('app/templates/auth/crear_tienda.html', tienda_html)
create_file('app/templates/config/tienda.html', config_tienda)
create_file('app/templates/config/categorias.html', config_cat)
create_file('app/templates/config/usuarios.html', config_usu)

print("Plantillas de autenticación y configuración generadas.")
