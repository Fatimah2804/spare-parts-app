from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Customer, Product, Order, OrderItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'tax_number']
    search_fields = ['name', 'phone', 'tax_number']
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_code', 'price', 'stock_quantity']
    search_fields = ['name', 'product_code']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'price', 'discount_percent', 'net_total_display']
    readonly_fields = ['net_total_display']

    def net_total_display(self, obj):
        if obj and obj.pk:
            return f"{obj.net_total():.2f}"
        return ""
    net_total_display.short_description = 'נטו אחרי הנחה'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = ['id', 'customer', 'created_at', 'status','is_printed',
    'is_delivered', 'order_total', 'view_order_link', 'view_invoice_link']

    def order_total(self, obj):
        return obj.get_total()
    order_total.short_description = 'סכום כולל'

    def view_order_link(self, obj):
        url = reverse('order_detail', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="padding:6px 12px; background:#4CAF50; color:white; border-radius:6px; text-decoration:none;">צפה בהזמנה</a>',
            url
        )
    view_order_link.short_description = 'פרטי הזמנה'

    def view_invoice_link(self, obj):
        url = reverse('invoice_detail', args=[obj.id])
        return format_html(
            '<a href="{}" target="_blank" style="padding:6px 12px; background:#2196F3; color:white; border-radius:6px; text-decoration:none;">חשבונית</a>',
            url
        )
    view_invoice_link.short_description = 'חשבונית'

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            old_status = old_obj.status
        else:
            old_status = None

        # אם ההזמנה בוטלה - לא לאפשר מסירה/הדפסה
        if obj.status == 'cancelled':
            obj.is_printed = False
            obj.is_delivered = False

        # אם עדיין לא הושלמה - גם לא לאפשר מסירה/הדפסה
        if obj.status != 'completed':
            obj.is_printed = False
            obj.is_delivered = False

        super().save_model(request, obj, form, change)

        if obj.status == 'completed' and not obj.stock_updated:
            obj.apply_stock()
            obj.save(update_fields=['stock_updated'])

        elif old_status == 'completed' and obj.status == 'cancelled' and obj.stock_updated:
            obj.restore_stock()
            obj.save(update_fields=['stock_updated'])