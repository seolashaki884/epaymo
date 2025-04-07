from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Document, Cart
from django.http import JsonResponse



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
        
        print(f"Email: {email}, Password: {password}") 
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email is not registered. Please check and try again.")
            return render(request, "core/login.html", {'email': email})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            
            if user.is_staff:
                return redirect('/admin/')  

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
        
        username = request.POST.get("username", "").strip()
        if not username:
            username = email.split('@')[0]  

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "core/signup.html", {"first_name": first_name, "last_name": last_name, "email": email})

        user = User.objects.create(first_name=first_name, last_name=last_name, email=email, username=username)
        user.set_password(password) 
        user.save()

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect("login")

    return render(request, "core/signup.html")

@login_required(login_url='login')
def add_to_cart(request, document_id):
    # Get the document
    document = Document.objects.get(id=document_id)
    
    # Check if the document already exists in the cart
    cart_item, created = Cart.objects.get_or_create(user=request.user, document=document)
    
    if not created:
        # If the item already exists, increase the quantity by 1
        cart_item.quantity += 1
        cart_item.save()

    # Return only the count of items in the cart as a JsonResponse
    return JsonResponse({'cart_item_count': request.user.cart_set.count()})

@login_required
def view_cart(request):
    # Fetch the cart items for the currently logged-in user
    cart_items = Cart.objects.filter(user=request.user)
    
    # Calculate the total price of the cart
    total_price = sum(item.total_price() for item in cart_items)
    
    return render(request, 'core/viewcart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

def test(request):
    return render(request, 'core/test.html')
 
def user_logout(request):
    logout(request) 
    return redirect('login')  