from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('equipment/add/', views.equipment, name='equipment'),
    path('dashboard/', views.dashboard, name='equipmentdashboard'),
    path('equipment/edit/', views.equipment_list, name='equipment_edit'),
    path('equipment/edit/<int:equipment_id>/', views.update_equipment, name='update_equipment'),
    path('equipment/delete/<int:equipment_id>/', views.delete_equipment, name='delete_equipment'),
    path('rental-request/create/', views.create_rental_request, name='create_rental_request'),
    path('rental-requests/', views.rental_requests_list, name='rental_requests_list'),
    path('rental/update-status/<int:rental_id>/', views.update_rental_status, name='update_rental_status'),
    path('rental-statistics/', views.rental_statistics_view, name='rental_statistics'),
    path('check-equipment-availability/<int:rental_id>/', views.check_equipment_availability, name='check_equipment_availability'),
    path('equipment/profile/', views.equipmentprofile, name='equipmentprofile'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)