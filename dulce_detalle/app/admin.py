from django.contrib import admin
from .models import (
    Negocio, CategoriaProducto, Producto,
    Venta, ItemVenta, Insumo,
    Pedido, ItemPedido, Nota,
)


# ── Negocio ───────────────────────────────────────────────────────────────

@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'slug', 'propietario', 'pedidos_pendientes_count')
    search_fields = ('nombre', 'slug', 'propietario__username')
    list_filter   = ('propietario',)
    readonly_fields = ('slug',)


# ── Categorías ────────────────────────────────────────────────────────────

@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'negocio')
    search_fields = ('nombre', 'negocio__nombre')
    list_filter   = ('negocio',)


# ── Productos ─────────────────────────────────────────────────────────────

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'negocio', 'categoria', 'precio', 'costo', 'stock', 'creado')
    search_fields = ('nombre', 'negocio__nombre')
    list_filter   = ('negocio', 'categoria')
    readonly_fields = ('creado', 'actualizado')
    list_editable  = ('stock',)


# ── Ventas ────────────────────────────────────────────────────────────────

class ItemVentaInline(admin.TabularInline):
    model  = ItemVenta
    extra  = 0
    readonly_fields = ('subtotal', 'ganancia')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'negocio', 'fecha', 'tipo', 'metodo_pago', 'total', 'creado')
    search_fields = ('negocio__nombre',)
    list_filter   = ('negocio', 'tipo', 'metodo_pago', 'fecha')
    readonly_fields = ('creado',)
    inlines       = [ItemVentaInline]


# ── Pedidos ───────────────────────────────────────────────────────────────

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'negocio', 'cliente_nombre', 'cliente_telefono', 'estado', 'total', 'creado')
    search_fields = ('cliente_nombre', 'cliente_telefono', 'negocio__nombre')
    list_filter   = ('negocio', 'estado')
    readonly_fields = ('creado',)
    inlines       = [ItemPedidoInline]


# ── Insumos ───────────────────────────────────────────────────────────────

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'negocio', 'costo_unitario', 'actualizado')
    search_fields = ('nombre', 'negocio__nombre')
    list_filter   = ('negocio',)
    readonly_fields = ('creado', 'actualizado')


# ── Notas ─────────────────────────────────────────────────────────────────

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display  = ('negocio', 'texto', 'creado')
    search_fields = ('texto', 'negocio__nombre')
    list_filter   = ('negocio',)
    readonly_fields = ('creado',)
