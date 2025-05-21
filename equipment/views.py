from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Equipment, RentalRequest
from core.models import UserProfile
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from datetime import datetime
from django.db.models import Sum, Count
from decimal import Decimal
from pathlib import Path
import os
from django.core.files.storage import default_storage
from django.db.models import Sum, Count, Case, When, Value, IntegerField

@login_required(login_url='login')
def equipment(request):

    # Check if the user has a profile and the correct category
    try:
        profile = request.user.userprofile
        if not profile.category or profile.category != 'equipment_rental':
            return redirect('error')
    except UserProfile.DoesNotExist:
        return redirect('error')  # Handle users without a profile
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        rental_rate = request.POST.get('rental_rate')
        status = request.POST.get('status')
        image = request.FILES.get('image')

        # Create the equipment
        new_equipment = Equipment.objects.create(
            name=name,
            description=description,
            rental_rate=rental_rate,
            status=status,
            image=image
        )

        # Log the addition of the new equipment
        content_type = ContentType.objects.get_for_model(Equipment)
        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=content_type.id,
            object_id=new_equipment.id,
            object_repr=str(new_equipment),
            action_flag=ADDITION,  # Action type: ADDITION (new object added)
            change_message=f"Added new equipment: {new_equipment.name}, {new_equipment.description}, Rental rate: {new_equipment.rental_rate}, Status: {new_equipment.status}"
        )

        messages.success(request, "Equipment successfully added!")
        return redirect('equipment')  # Redirect to the same page after adding

    equipment_list = Equipment.objects.order_by('-created_at')
    return render(request, 'equipment-admin/equipment-add.html', {
        'equipment_list': equipment_list
    })

@login_required(login_url='login')
@csrf_exempt
def update_equipment(request, equipment_id):
    if request.method == 'POST':
        try:
            if not request.content_type.startswith('multipart'):
                return JsonResponse({'status': 'error', 'message': 'Invalid form encoding'}, status=400)

            data = request.POST
            image = request.FILES.get('image')

            equipment = get_object_or_404(Equipment, id=equipment_id)

            old_name = equipment.name
            old_description = equipment.description
            old_rental_rate = equipment.rental_rate
            old_status = equipment.status

            equipment.name = data.get('name', equipment.name)
            equipment.description = data.get('description', equipment.description)
            equipment.rental_rate = data.get('rental_rate', equipment.rental_rate)
            equipment.status = data.get('status', equipment.status)

            if image:
                if equipment.image and default_storage.exists(equipment.image.path):
                    os.remove(equipment.image.path)
                equipment.image = image

            equipment.save()

            content_type = ContentType.objects.get_for_model(Equipment)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=equipment.id,
                object_repr=str(equipment),
                action_flag=CHANGE,
                change_message=(
                    f"Updated equipment: Name from '{old_name}' to '{equipment.name}', "
                    f"Description from '{old_description}' to '{equipment.description}', "
                    f"Rental rate from {old_rental_rate} to {equipment.rental_rate}, "
                    f"Status from '{old_status}' to '{equipment.status}'"
                )
            )

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required(login_url='login')
def delete_equipment(request, equipment_id):
    if request.method == 'POST':
        try:
            # Get the equipment instance to log before deletion
            equipment = Equipment.objects.get(id=equipment_id)

            # Log the deletion action
            content_type = ContentType.objects.get_for_model(Equipment)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=equipment.id,
                object_repr=str(equipment),
                action_flag=DELETION,  # Action type: Delete (object deleted)
                change_message=f"Deleted equipment: {equipment.name}, {equipment.description}, Rental rate: {equipment.rental_rate}, Status: {equipment.status}"
            )

            # Delete the equipment
            equipment.delete()

            return JsonResponse({'status': 'success', 'message': 'Equipment deleted successfully'})

        except Equipment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Equipment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
@login_required(login_url='login')
def create_rental_request(request):
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment_id')
        if not equipment_id:
            messages.error(request, "Equipment ID is missing.")
            return redirect('rentals')

        try:
            equipment = Equipment.objects.get(id=equipment_id)
        except Equipment.DoesNotExist:
            messages.error(request, "Selected equipment does not exist.")
            return redirect('rentals')

        try:
            rental_start_date = datetime.strptime(request.POST.get('rental_start_date'), "%Y-%m-%d").date()
            rental_end_date = datetime.strptime(request.POST.get('rental_end_date'), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            messages.error(request, "Invalid rental start or end date.")
            return redirect('rentals')

        today = timezone.now().date()

        if rental_start_date < today:
            messages.error(request, "Rental start date cannot be in the past.")
            return redirect('rentals')

        if rental_start_date > rental_end_date:
            messages.error(request, "Rental end date cannot be earlier than start date.")
            return redirect('rentals')

        # Check for a previous active or future rental request by the same user
        existing_request = RentalRequest.objects.filter(
            equipment=equipment,
            requested_by=request.user,
            rental_end_date__gte=today
        ).exclude(status='rejected').first()

        if existing_request:
            messages.error(request, "You already have an ongoing or upcoming rental request for this equipment.")
            return redirect('rentals')

        # Create the rental request
        RentalRequest.objects.create(
            equipment=equipment,
            requested_by=request.user,
            purpose=request.POST.get('purpose'),
            rental_start_date=rental_start_date,
            rental_end_date=rental_end_date,
            no_of_days_hours=request.POST.get('no_of_days_hours'),
        )

        messages.success(request, "Rental request submitted successfully.")
        return redirect('rentals')

    messages.error(request, "Invalid request method.")
    return redirect('rentals')  

@require_POST
def update_rental_status(request, rental_id):
    try:
        data = json.loads(request.body)
        status = data.get('status')

        if status not in dict(RentalRequest.STATUS_CHOICES):
            return HttpResponseBadRequest("Invalid status.")

        rental = get_object_or_404(RentalRequest, pk=rental_id)
        rental.status = status
        rental.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
def check_equipment_availability(request, rental_id):
    try:
        rental = RentalRequest.objects.select_related('equipment').get(pk=rental_id)
        equipment = rental.equipment

        # Check for other 'approved' requests for the same equipment that are not returned
        has_active_approved = RentalRequest.objects.filter(
            equipment=equipment,
            status='approved'
        ).exclude(pk=rental_id).exists()

        return JsonResponse({'has_active_approved': has_active_approved})
    except RentalRequest.DoesNotExist:
        return JsonResponse({'error': 'Rental not found'}, status=404)

@login_required(login_url='login')
def rental_requests_list(request):

    # Check if the user has a profile and the correct category
    try:
        profile = request.user.userprofile
        if not profile.category or profile.category != 'equipment_rental':
            return redirect('error')
    except UserProfile.DoesNotExist:
        return redirect('error')  # Handle users without a profile
    
    rental_requests = RentalRequest.objects.all()
    return render(request, 'equipment-admin/equipment-rentals.html', {'rental_requests': rental_requests})

@login_required(login_url='login')
def dashboard(request):

    # Check if the user has a profile and the correct category
    try:
        profile = request.user.userprofile
        if not profile.category or profile.category != 'equipment_rental':
            return redirect('error')
    except UserProfile.DoesNotExist:
        return redirect('error')  # Handle users without a profile
    logs = LogEntry.objects.filter(user=request.user).order_by('-action_time')
    return render(request, 'equipment-admin/dashboard.html', {'logs': logs})


@login_required(login_url='login')
def equipment_list(request):

    # Check if the user has a profile and the correct category
    try:
        profile = request.user.userprofile
        if not profile.category or profile.category != 'equipment_rental':
            return redirect('error')
    except UserProfile.DoesNotExist:
        return redirect('error')  # Handle users without a profile
    equipment_list = Equipment.objects.order_by('-created_at')
    return render(request, 'equipment-admin/equipment-edit.html', { 'equipment_list': equipment_list })

def rental_statistics_view(request):

    # Check if the user has a profile and the correct category
    try:
        profile = request.user.userprofile
        if not profile.category or profile.category != 'equipment_rental':
            return redirect('error')
    except UserProfile.DoesNotExist:
        return redirect('error')  # Handle users without a profile
    total_revenue = RentalRequest.objects.aggregate(total=Sum('total_rent_cost'))['total']
    if total_revenue is None:
        total_revenue = Decimal('0.00')

    total_rentals = RentalRequest.objects.count()

    top_equipment_rentals = (
        Equipment.objects
        .annotate(rental_count=Count('rental_requests'))
        .filter(rental_count__gt=0)
        .order_by('-rental_count')[:4]
    )

    context = {
        'total_revenue': total_revenue,
        'total_rentals': total_rentals,   
        'top_equipment_rentals': top_equipment_rentals,
    }
    return render(request, 'equipment-admin/dashboard.html', context)


login_required(login_url='login')
def equipmentprofile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'category': '',
            'region': '',
            'phone': 0,
            'address': '',
        }
    )

    if request.method == 'POST':
        user.first_name = request.POST.get('firstName', '')
        user.last_name = request.POST.get('lastName', '')
        user.save()

        profile.region = request.POST.get('organization', '')
        profile.phone = request.POST.get('phoneNumber') or 0
        profile.address = request.POST.get('address', '')

        # Handle profile image update
        if 'profile_image' in request.FILES:
            # Delete old image if it exists and is not default
            if profile.profile_image:
                old_image_path = Path(profile.profile_image.path)
                if old_image_path.is_file():
                    old_image_path.unlink()

            # Save new image
            profile.profile_image = request.FILES['profile_image']
        else:
            print("No file uploaded")

        # Handle password change - optional fields
        old_password = request.POST.get('oldPassword', '').strip()
        new_password = request.POST.get('newPassword', '').strip()
        confirm_new_password = request.POST.get('confirmNewPassword', '').strip()

        # Check if the user provided any passwords and validate if necessary
        if old_password or new_password or confirm_new_password:  # Only validate if any password field is filled
            if not old_password:
                messages.error(request, "Old password is required if you want to change the password.")
            elif not user.check_password(old_password):
                messages.error(request, "Old password is incorrect.")
            elif new_password != confirm_new_password:
                messages.error(request, "New passwords do not match.")
            elif new_password == "" or confirm_new_password == "":
                messages.error(request, "New password fields cannot be empty.")
            else:
                # If everything is valid, change the password
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in after password change
                messages.success(request, "Password updated successfully!")
                return redirect('equipmentprofile')  # Redirect to the profile page after successful password change

        profile.save()

        # Return to the profile page with error messages if password validation failed
        return redirect('equipmentprofile')
    return render(request, 'equipment-admin/equipment-profile.html', {'user': user, 'profile': profile})