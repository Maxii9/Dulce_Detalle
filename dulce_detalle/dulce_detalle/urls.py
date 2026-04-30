from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from app import views

urlpatterns = [
    # ── Panel Admin de Django ──
    # URL renombrada de /admin/ a /gestion-privada/ para reducir
    # el riesgo de ataques automatizados de bots que escanean /admin/.
    path('gestion-privada/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    
    # ── Autenticación y Cuentas (Globales) ──
    path('login/', views.user_login, name='login'),
    path('registro/', views.user_register, name='registro'),
    path('logout/', views.user_logout, name='logout'),
    path('onboarding/', views.crear_tienda_inicial, name='crear_tienda_inicial'),
    path('nueva-tienda/', views.crear_tienda_adicional, name='crear_tienda_adicional'),
    path('cambiar-tienda/<str:slug>/', views.cambiar_negocio, name='cambiar_negocio'),
    path('mis-productos/', views.inicio, name='lista_productos_global'),

    # ── Recuperación de Contraseña ──
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # ── Páginas Estáticas ──
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),

    # ── Gestión del Negocio (Dueño) ──
    path('<str:slug>/inactiva/', views.tienda_inactiva, name='tienda_inactiva'),
    path('<str:slug>/gestion/', include([
        path('', views.lista_productos, name='lista_productos'),
        
        # Productos
        path('productos/', views.lista_productos, name='lista_productos'),
        path('productos/nuevo/', views.crear_producto, name='crear_producto'),
        path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
        path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
        
        # Carrito de Gestión
        path('carrito/agregar/<int:pk>/', views.carrito_agregar, name='carrito_agregar'),
        path('carrito/quitar/<int:pk>/', views.carrito_quitar, name='carrito_quitar'),
        path('carrito/limpiar/', views.carrito_limpiar, name='carrito_limpiar'),
        path('carrito_libre/agregar/', views.carrito_libre_agregar_view, name='carrito_libre_agregar'),
        path('carrito_libre/quitar/<str:id_libre>/', views.carrito_libre_quitar_view, name='carrito_libre_quitar'),
        
        # Ventas
        path('ventas/', views.lista_ventas, name='lista_ventas'),
        path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),
        path('ventas/eliminar-masivo/', views.ventas_bulk_eliminar, name='ventas_bulk_eliminar'),
        path('ventas/<int:pk>/cambiar-tipo/', views.cambiar_tipo_venta, name='cambiar_tipo_venta'),
        path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),

        # Pedidos
        path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
        path('pedidos/<int:pk>/aceptar/', views.aceptar_pedido, name='aceptar_pedido'),
        path('pedidos/<int:pk>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),
        
        # Calculadora
        path('calculadora/', views.calculadora_costos, name='calculadora_costos'),
        path('calculadora/insumo/nuevo/', views.crear_insumo, name='crear_insumo'),
        path('calculadora/insumo/<int:pk>/editar/', views.editar_insumo, name='editar_insumo'),
        path('calculadora/insumo/<int:pk>/eliminar/', views.eliminar_insumo, name='eliminar_insumo'),
        
        # Notas
        path('notas/', views.lista_notas, name='lista_notas'),
        path('notas/<int:pk>/eliminar/', views.eliminar_nota, name='eliminar_nota'),

        # Configuración
        path('configurar/tienda/', views.configuracion_tienda, name='configuracion_tienda'),
        path('configurar/categorias/', views.configuracion_categorias, name='configuracion_categorias'),
        path('configurar/usuarios/', views.configuracion_usuarios, name='configuracion_usuarios'),
    ])),

    # ── Tienda Pública (Cliente) ──
    path('<str:slug>/tienda/', include([
        path('', views.tienda_publica, name='tienda_publica'),
        path('carrito/agregar/<int:pk>/', views.agregar_carrito_publico, name='agregar_carrito_publico'),
        path('carrito/quitar/<int:pk>/', views.quitar_carrito_publico, name='quitar_carrito_publico'),
        path('checkout/', views.checkout_publico, name='checkout_publico'),
        path('pedido/<int:pedido_id>/exito/', views.exito_publico, name='exito_publico'),
    ])),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
