from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Document


@login_required(login_url='login')
def home(request):
    documents = Document.objects.all()
    user = User.objects.all()
    print(f"Documents in View: {documents.count()}")
    return render(request, 'core/home.html', {'documents': documents, 'user':user})

def login_view(request):
    return render(request, 'core/login.html')

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        print(f"Email: {email}, Password: {password}")  # Debug statement

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email is not registered. Please check and try again.")
            return render(request, "core/login.html", {'email': email})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            
            # Redirect to admin panel if the user is staff
            if user.is_staff:
                return redirect('/admin/')  # Redirects staff to the Django admin page

            # Otherwise, redirect to home page
            return redirect("home")  # Redirect to home page after successful login
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

        # Ensure username is provided or generated
        username = request.POST.get("username", "").strip()
        if not username:
            username = email.split('@')[0]  # Use part of the email as username if not provided

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "core/signup.html", {"first_name": first_name, "last_name": last_name, "email": email})

        user = User.objects.create(first_name=first_name, last_name=last_name, email=email, username=username)
        user.set_password(password)  # Hash password
        user.save()

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect("login")

    return render(request, "core/signup.html")


def user_logout(request):
    logout(request)  # Logs out the user
    return redirect('login')  # Redirects to login page after logout