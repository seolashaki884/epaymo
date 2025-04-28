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
]





if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)