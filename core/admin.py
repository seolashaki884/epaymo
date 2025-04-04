from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from .models import Document, Cart


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'description', 'price')
    list_filter = ('category',) 
    search_fields = ('title', 'description')
    list_editable = ['price']
    actions_on_top = True

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'quantity', 'added_at', 'total_price')

    def total_price(self, obj):
        return obj.total_price()  # This is from the method you defined in the Cart model.
    total_price.short_description = 'Total Price'

    

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"), widget=forms.TextInput(attrs={"autofocus": True}))

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if email and password:
            try:
                user = User.objects.get(email=email) 
            except User.DoesNotExist:
                raise forms.ValidationError(_("Invalid email or password"))

            self.user_cache = authenticate(self.request, username=user.username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Invalid email or password"))
        return self.cleaned_data
admin.site.login_form = EmailAuthenticationForm
