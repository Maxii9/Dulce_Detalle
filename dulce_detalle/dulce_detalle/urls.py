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
    # Ventas
    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),
    path('ventas/<int:pk>/cambiar-tipo/', views.cambiar_tipo_venta, name='cambiar_tipo_venta'),
    path('estadisticas/', views.estadisticas_ventas, name='estadisticas_ventas'),
    # Notas
    path('notas/', views.lista_notas, name='lista_notas'),
    path('notas/<int:pk>/eliminar/', views.eliminar_nota, name='eliminar_nota'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
