from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('equipment/add/', views.equipment, name='equipment'),  # Add the trailing slash
    path('dashboard/', views.dashboard, name='equipmentdashboard'),


]






if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)