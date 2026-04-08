from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib import messages
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa
from io import BytesIO
from .models import Order, Customer, Product, OrderItem
import json
from django.contrib.auth.decorators import login_required

@login_required
def delivery_note(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'AJcarparts/delivery_note.html', {'order': order})

@login_required
def create_order(request):
    customers = Customer.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        items_json = request.POST.get("items")

        if not customer_id:
            return render(request, 'AJcarparts/create_order.html', {
                'customers': customers,
                'products': products,
                'error': "יש לבחור לקוח",
            })

        if not items_json:
            return render(request, 'AJcarparts/create_order.html', {
                'customers': customers,
                'products': products,
                'error': "לא נוספו מוצרים להזמנה",
            })

        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            return render(request, 'AJcarparts/create_order.html', {
                'customers': customers,
                'products': products,
                'error': "פורמט המוצרים אינו תקין",
            })

        if not items:
            return render(request, 'AJcarparts/create_order.html', {
                'customers': customers,
                'products': products,
                'error': "לא נוספו מוצרים להזמנה",
            })

        customer = get_object_or_404(Customer, id=customer_id)

        order = Order.objects.create(
            customer=customer,
            status='draft'
        )

        for item in items:
            product = get_object_or_404(Product, id=item['product_id'])

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int(item['quantity']),
                price=item['price'],
                discount_percent=item.get('discount_percent', 0)
            )

        if request.POST.get("finish_order") == "1":
            messages.success(request, f"ההזמנה #{order.id} נוצרה בהצלחה")
            return redirect('home')

        return redirect('order_detail', order_id=order.id)

    return render(request, 'AJcarparts/create_order.html', {
        'customers': customers,
        'products': products,
    })

@login_required
def home(request):
    customer_query = request.GET.get('customer', '')
    product_query = request.GET.get('product', '')

    orders = Order.objects.all().order_by('-created_at')

    if customer_query:
        orders = orders.filter(customer__name__icontains=customer_query)

    if product_query:
        orders = orders.filter(items__product__name__icontains=product_query).distinct()

    customers = Customer.objects.all().order_by('name')
    products = Product.objects.all().order_by('name')

    return render(request, 'AJcarparts/home.html', {
        'orders': orders,
        'customer_query': customer_query,
        'product_query': product_query,
        'customers': customers,
        'products': products,
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'AJcarparts/order_detail.html', {'order': order})

@login_required
def invoice_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'AJcarparts/invoice_detail.html', {'order': order})

@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response)

    y = 800
    p.drawString(100, y, f"Invoice #{order.id}")
    y -= 30
    p.drawString(100, y, f"Customer: {order.customer.name}")
    y -= 20
    p.drawString(100, y, f"Phone: {order.customer.phone}")
    y -= 20
    p.drawString(100, y, f"Status: {order.get_status_display()}")
    y -= 30

    p.drawString(100, y, "Products:")
    y -= 20

    for item in order.items.all():
        line = f"{item.product.name} | Qty: {item.quantity} | Price: {item.price} | Total: {item.get_total()}"
        p.drawString(100, y, line)
        y -= 20

    y -= 20
    p.drawString(100, y, f"Total: {order.get_total()}")

    p.showPage()
    p.save()
    return response

@login_required
def invoice_pdf_html(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    template = get_template('AJcarparts/invoice_detail.html')
    html = template.render({'order': order})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    pdf = pisa.CreatePDF(
        src=html,
        dest=response,
        encoding='UTF-8'
    )

    if pdf.err:
        return HttpResponse('אירעה שגיאה ביצירת ה-PDF')

    return response

@login_required
def update_order_status(request, order_id):
    if request.method != "POST":
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)

    new_status = request.POST.get("status")
    is_printed = request.POST.get("is_printed") == "on"
    is_delivered = request.POST.get("is_delivered") == "on"

    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
    if new_status not in valid_statuses:
        messages.error(request, "סטטוס לא חוקי")
        return redirect("home")

    old_status = order.status

    if new_status == "cancelled":
        is_printed = False
        is_delivered = False

    if new_status != "completed":
        is_printed = False
        is_delivered = False

    if old_status != new_status:
        if new_status == "completed" and not order.stock_updated:
            try:
                order.apply_stock()
            except ValueError as e:
                messages.error(request, str(e))
                return redirect("home")

        elif old_status == "completed" and new_status == "cancelled" and order.stock_updated:
            order.restore_stock()

    order.status = new_status
    order.is_printed = is_printed
    order.is_delivered = is_delivered
    order.save()

    messages.success(request, f"סטטוס הזמנה #{order.id} עודכן בהצלחה")
    return redirect("home")