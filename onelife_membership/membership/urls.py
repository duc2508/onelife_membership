from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import scan_qr

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='membership/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accumulate_points/', views.accumulate_points, name='accumulate_points'),
    path('redeem_voucher/', views.redeem_voucher, name='redeem_voucher'),
    path('use_voucher/<int:voucher_id>/', views.use_voucher, name='use_voucher'),
    path('apply_promo_code/', views.apply_promo_code, name='apply_promo_code'),
    path('calculate_shipping/', views.calculate_shipping, name='calculate_shipping'),
    path('anniversary_bonus/', views.anniversary_bonus, name='anniversary_bonus'),
    path('accounts/profile/', views.profile, name='profile'),
    path('scan-qr/', scan_qr, name='scan_qr'),
]