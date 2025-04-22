from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Document, Cart, Order
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from decimal import Decimal
import random
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from django.contrib.contenttypes.models import ContentType


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
            if user.is_staff:
                return redirect('/adminhome/') 

            return redirect("home") 
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

@login_required
@transaction.atomic
def submit_order(request):
    user = request.user

    # ✅ Always define cart_items first
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    # ✅ Use readable category names (optional)
    categories = list({item.document.category for item in cart_items})


    # Create the order with category (joined readable names)
    order = Order.objects.create(
        user=user,
        status='pending',
        category=", ".join(categories)
    )

    # Create OrderItems
    for cart_item in cart_items:
        order.order_items.create(
            document=cart_item.document,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.document.price,
        )

    # Finalize
    order.calculate_total_price()
    cart_items.delete()

    messages.success(request, "Order submitted successfully!")
    return redirect('home')

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    return render(request, 'core/orderlist.html', {'orders': orders})

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
        return render(request, 'access_denied.html')

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
            price=price  # Set the computed price
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


def biddings(request):
    orders = Order.objects.select_related('user').order_by('-ordered_at')
    return render(request, 'bac-admin/BAC-biddings.html', {'orders': orders})

def test(request):
    return render(request, 'core/test.html')
 
def user_logout(request):
    logout(request) 
    return redirect('login')  