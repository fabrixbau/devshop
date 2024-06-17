from django.contrib import admin

# Register your models here.
from .models import Categoria, Producto, Pedido, PedidoDetalle

admin.site.register(Categoria)
# admin.site.register(Producto) <---- ESTA ES LA FORMA DE ANTES DE HACERLO


@admin.register(Producto)  # <--------   ESTA ES LA NUEVA FORMA
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "precio",
        "categoria",
        "fecha_registro",
    )
    list_editable = (
        "precio",
        "categoria",
    )


# Inline para PedidoDetalle
class PedidoDetalleInline(admin.TabularInline):
    model = PedidoDetalle
    extra = 0  # No añadir filas extras automáticamente
    fields = ('producto', 'cantidad', 'subtotal')
    readonly_fields = ('producto', 'subtotal')


# Admin para Pedido
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('nro_pedido', 'cliente',
                    'fecha_registro', 'monto_total', 'estado')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('nro_pedido', 'cliente__usuario__username', 'estado')
    inlines = [PedidoDetalleInline]
