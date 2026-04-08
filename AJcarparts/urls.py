from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('create-order/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/invoice/', views.invoice_detail, name='invoice_detail'),
    path('orders/<int:order_id>/delivery-note/', views.delivery_note, name='delivery_note'),
    path('orders/<int:order_id>/invoice-pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('orders/<int:order_id>/invoice-pdf-html/', views.invoice_pdf_html, name='invoice_pdf_html'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),

    path('login/', auth_views.LoginView.as_view(template_name='AJcarparts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]