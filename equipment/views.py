from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Equipment, RentalRequest
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum, Count
from decimal import Decimal

@login_required(login_url='login')
def equipment(request):
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
            data = json.loads(request.body)  # Parse the JSON request body

            # Get the existing equipment
            equipment = get_object_or_404(Equipment, id=equipment_id)

            # Old values to log the changes
            old_name = equipment.name
            old_description = equipment.description
            old_rental_rate = equipment.rental_rate
            old_status = equipment.status

            # Update equipment fields
            equipment.name = data['name']
            equipment.description = data['description']
            equipment.rental_rate = data['rental_rate']
            equipment.status = data['status']
            equipment.save()

            # Log the update action
            content_type = ContentType.objects.get_for_model(Equipment)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=content_type.id,
                object_id=equipment.id,
                object_repr=str(equipment),
                action_flag=CHANGE,  # Action type: Change (existing object updated)
                change_message=f"Updated equipment: Name from '{old_name}' to '{equipment.name}', Description from '{old_description}' to '{equipment.description}', Rental rate from {old_rental_rate} to {equipment.rental_rate}, Status from '{old_status}' to '{equipment.status}'"
            )

            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        except Equipment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Equipment not found'}, status=404)
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

@login_required(login_url='login')
def rental_requests_list(request):
    rental_requests = RentalRequest.objects.all()
    return render(request, 'equipment-admin/equipment-rentals.html', {'rental_requests': rental_requests})

@login_required(login_url='login')
def dashboard(request):
    logs = LogEntry.objects.filter(user=request.user).order_by('-action_time')
    return render(request, 'equipment-admin/dashboard.html', {'logs': logs})


@login_required(login_url='login')
def equipment_list(request):
    equipment_list = Equipment.objects.order_by('-created_at')
    return render(request, 'equipment-admin/equipment-edit.html', { 'equipment_list': equipment_list })

def rental_statistics_view(request):
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