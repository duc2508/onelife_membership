from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import MembershipUserCreationForm
from .models import MembershipUser, Voucher
from datetime import datetime, timedelta
from geopy.distance import geodesic
import qrcode
import uuid
from io import BytesIO
import base64
# views.py
import cv2
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
# views.py
import base64

def scan_qr(request):
    if request.method == 'POST':
        if 'image' in request.POST:
            # Lấy dữ liệu hình ảnh từ request
            image_data = request.POST['image'].split(',')[1]
            image = base64.b64decode(image_data)
            img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)

            # Quét mã QR
            detect_qr = cv2.QRCodeDetector()
            data, bbox, _ = detect_qr(img)

            if data:
                return JsonResponse({'data': data})
            else:
                return JsonResponse({'data': 'Không tìm thấy mã QR'})

    return render(request, 'membership/scan_qr.html')

def scan_qr(request):
    if request.method == 'POST' and request.FILES['image']:
        # Lấy ảnh từ request
        image_file = request.FILES['image']
        image = np.fromstring(image_file.read(), np.uint8)
        img = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Quét mã QR
        detect_qr = cv2.QRCodeDetector()
        data, bbox, _ = detect_qr(img)

        if data:
            return JsonResponse({'data': data})
        else:
            return JsonResponse({'data': 'Không tìm thấy mã QR'})

    return render(request, 'membership/scan_qr.html')

def home(request):
    return render(request, 'membership/home.html')

def register(request):
    if request.method == 'POST':
        form = MembershipUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            MembershipUser.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            login(request, user)
            
            # Generate QR code
            qr = qrcode.make(str(user.id))
            buffered = BytesIO()
            qr.save(buffered, format="PNG")
            qr_image = base64.b64encode(buffered.getvalue()).decode()
            
            return render(request, 'membership/qr_code.html', {'qr_image': qr_image})
    else:
        form = MembershipUserCreationForm()
    return render(request, 'membership/register.html', {'form': form})
@login_required
def dashboard(request):
    membership_user = request.user.membershipuser
    vouchers = Voucher.objects.filter(user=request.user, used=False)
    return render(request, 'membership/dashboard.html', {'membership_user': membership_user, 'vouchers': vouchers})

@login_required
def accumulate_points(request):
    if request.method == 'POST':
        purchase_amount = float(request.POST['amount'])
        membership_user = request.user.membershipuser
        
        membership_user.total_spend += purchase_amount
        points_earned = calculate_points(membership_user.membership_level, purchase_amount)
        membership_user.points += points_earned
        
        update_membership_level(membership_user)
        
        membership_user.save()
        messages.success(request, f'You earned {points_earned} points!')
    return redirect('dashboard')

def calculate_points(membership_level, purchase_amount):
    points_per_1000 = {
        "Diamond": 5,
        "Platinum": 4,
        "Gold": 3,
        "Silver": 2,
        "Member": 1
    }
    return int((purchase_amount // 1000) * points_per_1000[membership_level])

def update_membership_level(membership_user):
    if membership_user.total_spend >= 4000000:
        membership_user.membership_level = "Diamond"
    elif membership_user.total_spend >= 3000000:
        membership_user.membership_level = "Platinum"
    elif membership_user.total_spend >= 2000000:
        membership_user.membership_level = "Gold"
    elif membership_user.total_spend >= 1000000:
        membership_user.membership_level = "Silver"

@login_required
def redeem_voucher(request):
    if request.method == 'POST':
        voucher_value = float(request.POST['voucher_value'])
        points_required = int(voucher_value * 0.2)  # 5 points per 1000 VND
        
        membership_user = request.user.membershipuser
        if membership_user.points >= points_required:
            membership_user.points -= points_required
            new_voucher = Voucher(
                user=request.user,
                value=voucher_value,
                expiry_date=timezone.now() + timedelta(days=7)
            )
            new_voucher.save()
            membership_user.save()
            messages.success(request, f'Voucher of {voucher_value} VND redeemed successfully!')
        else:
            messages.error(request, 'Not enough points to redeem this voucher.')
    return redirect('dashboard')

@login_required
def use_voucher(request, voucher_id):
    voucher = Voucher.objects.get(id=voucher_id)
    if voucher and voucher.user == request.user and not voucher.used and voucher.expiry_date > timezone.now():
        voucher.used = True
        voucher.save()
        messages.success(request, f'Voucher of {voucher.value} VND used successfully!')
    else:
        messages.error(request, 'Invalid or expired voucher.')
    return redirect('dashboard')

@login_required
def apply_promo_code(request):
    if request.method == 'POST':
        promo_code = request.POST['promo_code']
        purchase_amount = float(request.POST['purchase_amount'])
        
        valid_code = "XHNGH"
        discount = 50000
        start_date = datetime(2024, 10, 27)
        end_date = datetime(2024, 11, 6)
        
        if promo_code == valid_code and start_date <= timezone.now() <= end_date:
            discounted_amount = max(purchase_amount - discount, 0)
            messages.success(request, f'Promo code applied! Your new total is {discounted_amount} VND')
        else:
            messages.error(request, 'Invalid or expired promo code.')
    return redirect('dashboard')

@login_required
def calculate_shipping(request):
    if request.method == 'POST':
        purchase_amount = float(request.POST['purchase_amount'])
        customer_coords = (float(request.POST['lat']), float(request.POST['lon']))
        store_coords = (10.8231406, 106.6934509)  # Emart Phan Văn Trị coordinates
        
        distance = geodesic(customer_coords, store_coords).kilometers
        shipping_fee = calculate_shipping_fee(request.user.membershipuser.membership_level, distance, purchase_amount)
        
        messages.info(request, f'Shipping fee: {shipping_fee} VND')
    return redirect('dashboard')

def calculate_shipping_fee(membership_level, distance, purchase_amount):
    base_fee = 40000
    if membership_level in ["Gold", "Platinum", "Diamond"] and distance <= 5:
        return 0
    elif (membership_level == "Member" or membership_level == "Silver") and distance <= 5 and purchase_amount >= 500000:
        return max(base_fee - 35000, 0)
    return base_fee

@login_required
def anniversary_bonus(request):
    membership_user = request.user.membershipuser
    today = timezone.now().date()
    registration_anniversary = membership_user.registration_date.date() + timedelta(days=365)
    
    if today == registration_anniversary:
        membership_user.points += 10000
        membership_user.save()
        messages.success(request, 'Happy anniversary! You received a 10,000 point bonus!')
    else:
        messages.info(request, 'No anniversary bonus available at this time.')
    return redirect('dashboard')

@login_required
def profile(request):
    return render(request, 'membership/profile.html')  