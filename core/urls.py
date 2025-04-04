from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),  # Add the trailing slash
    path('', views.login_view, name='login'),  # Login page
    path('user_login/', views.user_login, name='user_login'),  # POST login submission
    path("signup/", views.signup, name="signup"),   
    path('logout/', views.user_logout, name='user_logout'),
    path('add-to-cart/<int:document_id>/', views.add_to_cart, name='add_to_cart'),  
    path('test/', views.test, name='test')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
