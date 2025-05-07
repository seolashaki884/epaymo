from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Document, Cart, Bid, Billing
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
from .models import UserProfile
from equipment.models import Equipment
import random
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import now as timezone_now
import pytz
import base64
import requests
import uuid
import logging
logger = logging.getLogger(__name__)


@login_required(login_url='login')
def home(request):
    # Get category filter from query parameters
    category_filter = request.GET.get('category') 
    
    # Get search query from GET request
    search_query = request.GET.get('search', '') 
    
    # Filter documents based on the category and search query (if provided)
    if category_filter:
        documents = Document.objects.filter(category=category_filter)
    else:
        documents = Document.objects.all()
    
    if search_query:
        documents = documents.filter(title__icontains=search_query)  # Filter by title
    
    # Order the filtered documents by ID
    documents = documents.order_by('-id')

    # Get all the unique categories to display in the filter dropdown
    categories = dict(Document.CATEGORY_CHOICES)

    user = User.objects.all()
    print(f"Documents in View: {documents.count()}")

    return render(request, 'core/home.html', {
        'documents': documents, 
        'user': user,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query  # Pass the search query back to the template
    })

def login_view(request):
    return render(request, 'core/login.html')

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email is not registered. Please check and try again.")
            return render(request, "core/login.html", {'email': email})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                return redirect('/admin/') 

            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.category == 'bidding_documents':
                    return redirect('admin-home')  # path('adminhome/', ...)
                elif user_profile.category == 'equipment_rental':
                    return redirect('equipmentdashboard')
                else:
                    return redirect('homeboot')
            except UserProfile.DoesNotExist:
                # No UserProfile found, fallback
                if user.is_staff:
                    return redirect('/home/')
                return redirect('homeboot')

        else:
            messages.error(request, "Invalid password. Please try again.")
            return render(request, "core/login.html", {'email': email})

    return render(request, "core/login.html")



def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "core/signup.html", {"first_name": first_name, "last_name": last_name, "email": email})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "core/signup.html", {"first_name": first_name, "last_name": last_name, "email": email})

        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "core/signup.html", {"first_name": first_name, "last_name": last_name, "email": email})

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Store user info + OTP in session
        request.session['signup_data'] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "username": username,
            "password": password,
            "otp": otp
        }

        # Send OTP to email
        send_mail(
            subject="Your One-Time Password (OTP) for Account Verification",
            message=(
                f"Dear {first_name},\n\n"
                f"Thank you for signing up at Epaymo.\n\n"
                f"Your One-Time Password (OTP) for verifying your email address is:\n\n"
                f"{otp}\n\n"
                f"This OTP is valid for 10 minutes. Please do not share it with anyone.\n\n"
                f"If you did not initiate this request, please ignore this email.\n\n"
                f"Best regards,\n"
                f"The Epaymo Team"
            ),
            from_email="epaymonia@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("verify_otp")

    return render(request, "core/signup.html")

def verify_otp(request):
    signup_data = request.session.get("signup_data")

    if not signup_data:
        messages.error(request, "Session expired or invalid access.")
        return redirect("signup")

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if entered_otp == signup_data["otp"]:
            user = User.objects.create(
                first_name=signup_data["first_name"],
                last_name=signup_data["last_name"],
                email=signup_data["email"],
                username=signup_data["username"]
            )
            user.set_password(signup_data["password"])
            user.save()

            # Clear session data
            del request.session["signup_data"]

            messages.success(request, "Account created successfully!")
            return redirect("login")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "core/verify_otp.html")


@login_required(login_url='login')
def add_to_cart(request, document_id):
    # Get the document
    document = Document.objects.get(id=document_id)
    
    cart_item, created = Cart.objects.get_or_create(user=request.user, document=document)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({'cart_item_count': request.user.cart_set.count()})

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
  
    total_price = sum(item.total_price() for item in cart_items)
    
    return render(request, 'core/viewcart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()

        # Render the updated cart view as HTML
        return render(request, 'core/viewcart.html')  # Update with the correct template path for your cart view
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@require_POST
def update_cart_quantity(request):
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity'))
        cart_item = Cart.objects.get(id=item_id, user=request.user)

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()

            # Recalculate total cart value
            cart_items = Cart.objects.filter(user=request.user)
            cart_total = sum(item.total_price() for item in cart_items)

            return JsonResponse({
                'status': 'success',
                'new_total': cart_item.total_price(),
                'cart_total': cart_total
            })

        else:
            cart_item.delete()

            cart_items = Cart.objects.filter(user=request.user)
            cart_total = sum(item.total_price() for item in cart_items)

            return JsonResponse({
                'status': 'removed',
                'cart_total': cart_total
            })

    except (Cart.DoesNotExist, ValueError):
        return JsonResponse({'status': 'error'}, status=400)

def get_cart_count(request):
    # Get the cart count for the logged-in user
    cart_count = request.user.cart_set.count()
    return JsonResponse({'cart_count': cart_count})

@login_required
def billing_prep(request):
    return render(request, 'core/billingprep.html')


def adminhome(request):
    # Ensure that the logged-in user is a staff member
    if not request.user.is_staff:
        return render(request, 'core/login.html')

    # Filter logs for the logged-in user
    logs = LogEntry.objects.filter(user=request.user).order_by('-action_time')

    return render(request, 'bac-admin/dashboard.html', {'logs': logs})


def BAC(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        raw_price = request.POST.get('abc')
        abc = Decimal(raw_price.replace(',', ''))
        category = request.POST.get('category')
        region = request.POST.get('region')
        image = request.FILES.get('image')

        bidding_start_date = request.POST.get('bidding_start_date')
        bidding_end_date = request.POST.get('bidding_end_date')

        bidding_start = datetime.strptime(bidding_start_date, "%Y-%m-%dT%H:%M")
        bidding_end = datetime.strptime(bidding_end_date, "%Y-%m-%dT%H:%M")

        # Compute price based on the abc value
        if abc < 500000:
            price = Decimal(500)
        elif 500000 <= abc < 1000000:
            price = Decimal(1000)
        elif 1000000 <= abc < 5000000:
            price = Decimal(5000)
        elif 5000000 <= abc < 10000000:
            price = Decimal(10000)
        elif 10000000 <= abc < 50000000:
            price = Decimal(25000)
        elif 50000000 <= abc < 500000000:
            price = Decimal(50000)
        else:
            price = Decimal(75000)

        # Create the Document object
        document = Document.objects.create(
            title=title,
            description=description,
            abc=abc,
            category=category,
            region=region,
            image=image,
            price=price,
            bidding_start_date=bidding_start,
            bidding_end_date=bidding_end
        )

        # Log the creation of the document in the admin logs
        content_type = ContentType.objects.get_for_model(Document)  # Get content type for Document model
        LogEntry.objects.log_action(
            user_id=request.user.id,  # The user who created the document
            content_type_id=content_type.id,
            object_id=document.id,
            object_repr=str(document),  # String representation of the document
            action_flag=ADDITION,  # Action type: ADDITION (new object created)
            change_message=f"Document '{document.title}' created with price {document.price}"
        )

        messages.success(request, 'Document published successfully!')
        return redirect('bac-add')

    documents = Document.objects.filter(category='bidding_documents').order_by('-id')
    return render(request, 'bac-admin/BAC-add.html', {'documents': documents})

def bac_edit(request):
    documents = Document.objects.all().order_by('-id')
    return render(request, 'bac-admin/BAC-edit.html', {'documents': documents})

@csrf_exempt
def update_document(request, doc_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            document = Document.objects.get(id=doc_id)

            abc_raw = data['abc']
            abc = Decimal(abc_raw.replace(',', '')) if isinstance(abc_raw, str) else Decimal(abc_raw)

            if abc < 500000:
                price = Decimal(500)
            elif 500000 <= abc < 1000000:
                price = Decimal(1000)
            elif 1000000 <= abc < 5000000:
                price = Decimal(5000)
            elif 5000000 <= abc < 10000000:
                price = Decimal(10000)
            elif 10000000 <= abc < 50000000:
                price = Decimal(25000)
            elif 50000000 <= abc < 500000000:
                price = Decimal(50000)
            else:
                price = Decimal(75000)

            start_date = datetime.strptime(data['bidding_start_date'], "%Y-%m-%dT%H:%M")
            end_date = datetime.strptime(data['bidding_end_date'], "%Y-%m-%dT%H:%M")

            # Update document fields
            old_title = document.title  # Store old title for logging
            old_description = document.description  # Store old description for logging
            old_abc = document.abc  # Store old abc for logging
            old_region = document.region  # Store old region for logging
            old_price = document.price  # Store old price for logging

            document.title = data['title']
            document.description = data['description']
            document.abc = abc
            document.region = data['region']
            document.price = price  # ✅ Auto-updated price
            document.bidding_start_date = start_date
            document.bidding_end_date = end_date
            document.save()

            # Log the document update in admin logs
            content_type = ContentType.objects.get_for_model(Document)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=document.id,
                object_repr=str(document),
                action_flag=CHANGE,  # Action type: CHANGE (existing object updated)
                change_message=f"Updated document from title '{old_title}' to '{document.title}', description '{old_description}' to '{document.description}', ABC from {old_abc} to {document.abc}, price from {old_price} to {document.price}, and region from '{old_region}' to '{document.region}'."
            )

            return JsonResponse({'status': 'success'})

        except Document.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Document not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def delete_document(request, doc_id):
    if request.method == 'POST':
        try:
            # Safely parse JSON body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON body'}, status=400)

            # Check if method override is DELETE
            if data.get('_method') != 'DELETE':
                return JsonResponse({'status': 'error', 'message': 'Invalid method override'}, status=400)

            # Get the document
            document = Document.objects.get(id=doc_id)
            document_repr = str(document)  # Save for logging before deletion
            document_id = document.id

            # Delete document
            document.delete()

            # Log deletion
            content_type = ContentType.objects.get_for_model(Document)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=document_id,
                object_repr=document_repr,
                action_flag=DELETION,
                change_message=f"Deleted document '{document_repr}'"
            )

            return JsonResponse({'status': 'success'})

        except Document.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Document not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


def rentals(request):
    equipment_list = Equipment.objects.filter(status='Available')
    return render(request, 'core/bootequipment_rental.html', {'equipment_list': equipment_list})

def biddings(request):
    bids = Bid.objects.order_by('-bid_time')
    return render(request, 'bac-admin/BAC-biddings.html', {'bids': bids})

def get_bid_json(request, bid_id):
    try:
        bid = Bid.objects.select_related('user', 'document').get(id=bid_id)
        return JsonResponse({
            'id': bid.id,
            'document_title': bid.document.title,
            'user_full_name': bid.user.get_full_name() or bid.user.username,
            'proposed_price': str(bid.proposed_price),
            'status': bid.status,
        })
    except Bid.DoesNotExist:
        return JsonResponse({'error': 'Bid not found'}, status=404)

@csrf_exempt  # only use this in development — better to use @require_POST with CSRF
def update_bid_status(request, bid_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            bid = Bid.objects.get(id=bid_id)
            bid.status = status
            bid.save()
            return JsonResponse({'success': True})
        except Bid.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Bid not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def rentalform(request):
    return render(request, 'core/rentalform.html')

def test(request):
    return render(request, 'core/test.html')
 
def user_logout(request):
    logout(request) 
    return redirect('login')  

def document_json(request, pk):
    try:
        doc = Document.objects.get(pk=pk)
        
        # Format the start and end dates
        start_date = doc.bidding_start_date.strftime('%b %d, %Y %I:%M %p')  # e.g., May 07, 2025 09:34 PM
        end_date = doc.bidding_end_date.strftime('%b %d, %Y %I:%M %p')    # e.g., May 12, 2025 08:33 AM
        
        return JsonResponse({
            "title": doc.title,
            "description": doc.description,
            "category": doc.get_category_display(),
            "price": str(doc.price),
            "region": doc.region,
            "image": doc.image.url if doc.image else None,
            "bidding_start_date": start_date,
            "bidding_end_date": end_date,
        })
    except Document.DoesNotExist:
        raise Http404("Document not found")
    
@login_required
def place_bid(request):
    if request.method == 'POST':
        document_id = request.POST.get('document_id')

        try:
            document = Document.objects.get(id=document_id)
            user = request.user

            # Optional: Prevent duplicate bids
            if Bid.objects.filter(user=user, document=document).exists():
                return JsonResponse({'error': 'You have already placed a bid on this document.'}, status=400)

            bid = Bid.objects.create(
                user=user,
                document=document,
                proposed_price=document.price
            )

            return JsonResponse({'message': 'Bid placed successfully.'})

        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def create_paymaya_payment(request, bid_id):
    if request.method == 'POST':
        try:
            bid = Bid.objects.get(id=bid_id, status='approved')
        except Bid.DoesNotExist:
            return JsonResponse({"success": False, "error": "Bid not found or not approved."})

        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        email = request.user.email
        phone = request.POST.get('number')

        invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"

        billing, created = Billing.objects.update_or_create(
            bid=bid,
            defaults={
                'full_name': full_name,
                'address': address,
                'email_add': email,
                'number': phone or None,
                'invoice_number': invoice_number,
                'amount': bid.proposed_price,
                'payment_status': 'pending',
                'issued_date': timezone.now()
            }
        )

        payload = {
            "totalAmount": {
                "value": float(bid.proposed_price),
                "currency": "PHP"
            },
            "buyer": {
                "firstName": full_name.split()[0],
                "lastName": ' '.join(full_name.split()[1:]) or 'N/A',
                "contact": {
                    "email": email,
                    "phone": phone or "0000000000"
                },
                "billingAddress": {
                    "line1": address,
                    "countryCode": "PH"
                }
            },
            "redirectUrl": {
                "success": f"http://127.0.0.1:8001/payment/success/{billing.id}/",
                "failure": f"http://127.0.0.1:8001/payment/failure/{billing.id}/",
                "cancel": f"http://127.0.0.1:8001/payment/cancel/{billing.id}/"
            },
            "requestReferenceNumber": invoice_number
        }

        secret_key = "pk-Z0OSzLvIcOI2UIvDhdTGVVfRSSeiGStnceqwUE7n0Ah"
        basic_auth = base64.b64encode(f"{secret_key}:".encode()).decode()

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            'https://pg-sandbox.paymaya.com/checkout/v1/checkouts',
            json=payload,
            headers=headers
        )

        logger.info(f"PayMaya response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            return JsonResponse({"success": True, "redirectUrl": data['redirectUrl']})
        else:
            logger.error(f"PayMaya Error: {response.text}")  # Log the error message for better troubleshooting
            return JsonResponse({"success": False, "error": response.text})

def payment_success(request, billing_id):
    billing = get_object_or_404(Billing, id=billing_id)
    billing.payment_status = 'paid'
    billing.payment_date = timezone.now()

    bid = billing.bid
    bid.status = 'paid'
    bid.save()
    billing.save()
    messages.success(request, "Payment successful!")
    return redirect('/my-bids/')

def payment_failure(request, billing_id):
    messages.error(request, "Payment failed. Please try again.")
    return redirect('/my-bids/')

def payment_cancel(request, billing_id):
    messages.warning(request, "Payment was cancelled.")
    return redirect('/my-bids/')


def submit_billing_info(request, bid_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            bid = Bid.objects.get(id=bid_id)
            full_name = request.POST.get('full_name')
            address = request.POST.get('address')
            email = request.POST.get('email_add')
            phone = request.POST.get('number')

            invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"

            # Logging form data
            logger.info(f"Submitting billing info for bid {bid_id}: {full_name}, {address}, {email}, {phone}")

            Billing.objects.update_or_create(
                bid=bid,
                defaults={
                    'full_name': full_name,
                    'address': address,
                    'email_add': email,
                    'number': phone or None,
                    'invoice_number': invoice_number,
                    'amount': bid.proposed_price,
                    'issued_date': timezone.now()
                }
            )

            return JsonResponse({'success': True})
        except Bid.DoesNotExist:
            logger.error(f"Bid {bid_id} not found.")
            return JsonResponse({'success': False, 'error': 'Bid not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
    
def equipment_json(request, pk):
    try:
        eq = Equipment.objects.get(pk=pk)
        return JsonResponse({
            'name': eq.name,
            'description': eq.description,
            'status': eq.status,
            'rental_rate': str(eq.rental_rate),
            'image': request.build_absolute_uri(eq.image.url) if eq.image else None,
        })
    except Equipment.DoesNotExist:
        raise Http404("Equipment not found")


def homebootstrap(request):
      # Get category filter from query parameters
    category_filter = request.GET.get('category') 
    
    # Get search query from GET request
    search_query = request.GET.get('search', '') 
    
    # Filter documents based on the category and search query (if provided)
    if category_filter:
        documents = Document.objects.filter(category=category_filter)
    else:
        documents = Document.objects.all()
    
    if search_query:
        documents = documents.filter(title__icontains=search_query)  # Filter by title
    
    # Order the filtered documents by ID
    documents = documents.order_by('-id')

    # Get all the unique categories to display in the filter dropdown
    categories = dict(Document.CATEGORY_CHOICES)

    manila_tz = pytz.timezone('Asia/Manila')
    now = timezone.now().astimezone(manila_tz)

    # Convert document's bidding_end_date to Asia/Manila timezone
    for document in documents:
        if document.bidding_end_date:
            document.bidding_end_date = document.bidding_end_date.astimezone(manila_tz)


    user = User.objects.all()
    print(f"Documents in View: {documents.count()}")
    return render(request, 'core/bootbidding_documents.html', {
        'documents': documents, 
        'user': user,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query,  # Pass the search query back to the template
        'now': now,

    })

@login_required
def my_bids_list(request):
    bids = Bid.objects.filter(user=request.user).select_related('document').order_by('-bid_time')
    
    context = {
        'bids': bids,
    }
    return render(request, 'core/bootbid_list.html', context)
