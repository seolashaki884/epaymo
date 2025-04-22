from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Equipment
from django.db import transaction
from decimal import Decimal
import random
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
@login_required(login_url='login')
def equipment(request):
    equipment_list = Equipment.objects.filter(status='available').order_by('-created_at')
    return render(request, 'core/equipment_rental.html', {
        'equipment_list': equipment_list
    })

