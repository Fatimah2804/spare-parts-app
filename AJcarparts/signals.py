from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import OrderItem


@receiver(post_delete, sender=OrderItem)
def restore_stock_on_delete(sender, instance, **kwargs):
    if instance.product:
        instance.product.stock_quantity += instance.quantity
        instance.product.save()