from django.db import models
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name="שם לקוח")
    phone = models.CharField(max_length=20, verbose_name="טלפון")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="כתובת")
    tax_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='ע.מ / ח.פ')
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="שם מוצר")
    product_code = models.CharField(max_length=100, unique=True, verbose_name="קוד מוצר")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="מחיר")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="כמות במלאי")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")

    def __str__(self):
        return f"{self.name} ({self.product_code})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'טיוטה'),
        ('completed', 'הושלמה'),
        ('cancelled', 'בוטלה'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="לקוח")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="תאריך")
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="סטטוס")

    is_printed = models.BooleanField(default=False, verbose_name="הודפסה")
    is_delivered = models.BooleanField(default=False, verbose_name="נמסרה")

    stock_updated = models.BooleanField(default=False, verbose_name="מלאי עודכן")

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def total_after_discount(self):
        return sum(item.net_total() for item in self.items.all())

    def vat_amount(self):
        return self.total_after_discount() * Decimal('0.18')

    def total_without_vat(self):
        return self.total_after_discount()

    def total_with_vat(self):
        return self.total_after_discount() + self.vat_amount()

    def apply_stock(self):
        for item in self.items.all():
            if item.product.stock_quantity < item.quantity:
                raise ValueError(f"אין מספיק מלאי עבור {item.product.name}")

        for item in self.items.all():
            item.product.stock_quantity -= item.quantity
            item.product.save()

        self.stock_updated = True

    def restore_stock(self):
        for item in self.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()

        self.stock_updated = False

    def __str__(self):
        return f"הזמנה #{self.id} - {self.customer.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="הזמנה")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="מוצר")
    quantity = models.PositiveIntegerField(verbose_name="כמות")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="מחיר ליחידה",
        blank=True,
        null=True
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="הנחה באחוזים"
    )

    def save(self, *args, **kwargs):
        if self.product and self.price is None:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def get_total(self):
        return self.quantity * self.price

    def discount_amount(self):
        return (self.get_total() * self.discount_percent) / Decimal('100')

    def net_total(self):
        return self.get_total() - self.discount_amount()

    def unit_price_after_discount(self):
        return self.price - ((self.price * self.discount_percent) / Decimal('100'))

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"