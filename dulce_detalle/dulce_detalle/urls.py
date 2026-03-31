from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('negocio/<str:slug>/', views.cambiar_negocio, name='cambiar_negocio'),
    path('producto/nuevo/', views.crear_producto, name='crear_producto'),
    path('producto/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    # Carrito
    path('carrito/agregar/<int:pk>/', views.carrito_agregar, name='carrito_agregar'),
    path('carrito/quitar/<int:pk>/', views.carrito_quitar, name='carrito_quitar'),
    path('carrito/limpiar/', views.carrito_limpiar, name='carrito_limpiar'),
    path('carrito_libre/agregar/', views.carrito_libre_agregar_view, name='carrito_libre_agregar'),
    path('carrito_libre/quitar/<str:id_libre>/', views.carrito_libre_quitar_view, name='carrito_libre_quitar'),
    
    # ── Autenticación y Cuentas ──
    path('login/', views.user_login, name='login'),
    path('registro/', views.user_register, name='registro'),
    path('logout/', views.user_logout, name='logout'),
    path('tienda/nueva/', views.crear_tienda_inicial, name='crear_tienda_inicial'),
    
    # ── Configuración ──
    path('configurar/tienda/', views.configuracion_tienda, name='configuracion_tienda'),
    path('configurar/productos/', views.configuracion_categorias, name='configuracion_categorias'),
    path('configurar/usuarios/', views.configuracion_usuarios, name='configuracion_usuarios'),

    # ── Ventas ──
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),
    path('ventas/eliminar-masivo/', views.ventas_bulk_eliminar, name='ventas_bulk_eliminar'),
    path('ventas/<int:pk>/cambiar-tipo/', views.cambiar_tipo_venta, name='cambiar_tipo_venta'),
    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    # Calculadora de Costos
    path('calculadora/', views.calculadora_costos, name='calculadora_costos'),
    path('calculadora/insumo/nuevo/', views.crear_insumo, name='crear_insumo'),
    path('calculadora/insumo/<int:pk>/editar/', views.editar_insumo, name='editar_insumo'),
    path('calculadora/insumo/<int:pk>/eliminar/', views.eliminar_insumo, name='eliminar_insumo'),
    
    # ── Pedidos (Administrador) ──
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/<int:pk>/aceptar/', views.aceptar_pedido, name='aceptar_pedido'),
    path('pedidos/<int:pk>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),
    
    # ── Tienda Pública (Cliente) ──
    path('tienda/<str:slug>/', views.tienda_publica, name='tienda_publica'),
    path('tienda/<str:slug>/carrito/agregar/<int:pk>/', views.agregar_carrito_publico, name='agregar_carrito_publico'),
    path('tienda/<str:slug>/carrito/quitar/<int:pk>/', views.quitar_carrito_publico, name='quitar_carrito_publico'),
    path('tienda/<str:slug>/checkout/', views.checkout_publico, name='checkout_publico'),
    path('tienda/<str:slug>/pedido/<int:pedido_id>/exito/', views.exito_publico, name='exito_publico'),

    # Notas
    path('notas/', views.lista_notas, name='lista_notas'),
    path('notas/<int:pk>/eliminar/', views.eliminar_nota, name='eliminar_nota'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
