from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.conf.urls import handler404
from django.shortcuts import render

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
    path('get_bid_details/<int:bid_id>/', views.get_bid_details, name='get_bid_details'),
    path('cancel_bid/<int:bid_id>/', views.cancel_bid, name='cancel_bid'),

    path('bids/<int:bid_id>/billing/form/', views.submit_billing_info, name='submit_billing_info'),
    path('bids/<int:bid_id>/create-paymaya-payment/', views.create_paymaya_payment, name='create_paymaya_payment'),
    path('payment/billing/success/<int:billing_id>/', views.payment_success, name='payment_success'),
    path('payment/billing/failure/<int:billing_id>/', views.payment_failure, name='payment_failure'),
    path('payment/billing/cancel/<int:billing_id>/', views.payment_cancel, name='payment_cancel'),
    path('my-bids/', views.my_bids_list, name='mybids'),
    path('homeboot/', views.homebootstrap, name='homeboot' ),
    path('documents/<int:pk>/json/', views.document_json, name='document_json'),
    path('equipments/<int:pk>/json/', views.equipment_json, name='equipment_json'),
    path('user/profile/', views.profile, name='userProfile'),
    path('validate_old_password/', views.validate_old_password, name='validate_old_password'),
    path('finance-dashboard/', views.financedashboard, name='finance_dashboard'),
    path('error/', views.error, name='error'),
    path('export/pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),
    path('export/excel/', views.export_transactions_excel, name='export_transactions_excel'),
    path('finance/profile/', views.financeprofile, name='finance-profile'),
    path('BAC/profile/', views.bacprofile, name='bacprofile'),
    path('rental/requests/', views.rental_request_list, name='rental_request_list'),
    path('payment/rental/success/<int:rental_id>/', views.rental_payment_success, name='rental_payment_success'),
    path('payment/rental/failure/<int:rental_id>/', views.rental_payment_failure, name='rental_payment_failure'),
    path('payment/rental/cancel/<int:rental_id>/', views.rental_payment_cancel, name='rental_payment_cancel'),
    path('rental/create-payment/', views.create_rental_payment, name='create_rental_payment'),

]
handler404 = 'core.views.custom_404_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
