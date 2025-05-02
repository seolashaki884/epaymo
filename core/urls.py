from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('home/', views.home, name='home'), 
    path('', views.login_view, name='login'), 
    path('user_login/', views.user_login, name='user_login'),
    path("signup/", views.signup, name="signup"),   
    path('logout/', views.user_logout, name='user_logout'),
    path('add-to-cart/<int:document_id>/', views.add_to_cart, name='add_to_cart'),  
    path('view-cart/', views.view_cart, name='view_cart'),    
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('get_cart_count/', views.get_cart_count, name='get_cart_count'),
    path('billing-preparation/', views.billing_prep, name='billing-prep'),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path('adminhome/', views.adminhome, name='admin-home'),
    path('BAC/', views.BAC, name='bac-add'),
    path('BAC/edit', views.bac_edit, name='bac-edit'),
    path('bac-edit/<int:doc_id>/update/', views.update_document, name='update_document'),
    path('delete-document/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('biddings/', views.biddings, name='biddings'),
    path('test/', views.test, name='test'),
    path('rentals/', views.rentals, name='rentals'),
    path('rental-form/', views.rentalform, name='rental-form' ),
    path('place-bid/', views.place_bid, name='place_bid'),
    path('bids/<int:bid_id>/json/', views.get_bid_json, name='bid_json'),
    path('bids/<int:bid_id>/update/', views.update_bid_status, name='update_bid'),




    path('my-bids/', views.my_bids_list, name='mybids'),
    path('homeboot/', views.homebootstrap, name='homeboot' ),
    path('documents/<int:pk>/json/', views.document_json, name='document_json'),
    path('equipments/<int:pk>/json/', views.equipment_json, name='equipment_json'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
