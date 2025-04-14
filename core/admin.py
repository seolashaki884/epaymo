from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.contrib.humanize.templatetags.humanize import intcomma  # Import intcomma for formatting
from .models import Document, Cart, Order
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        exclude = ('password',)  # This hides the password from the form


class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    fieldsets = (
        (None, {'fields': ('username', 'email', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


# Unregister original UserAdmin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'description', 'formatted_price')  # Add 'price' here
    list_filter = ('category',) 
    search_fields = ('title', 'description')
    actions_on_top = True

    def formatted_price(self, obj):
        return f"₱ {intcomma(f'{obj.price:.2f}')}"
    formatted_price.short_description = 'Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'get_formatted_total_price', 'ordered_at', 'status',)
    list_display_links = ('user_full_name',)
    list_filter = ('status',)
    readonly_fields = ['user_full_name_display', 'total_price', 'ordered_at']
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    actions_on_top = True
    exclude = ['user'] 

    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'User'

    def get_formatted_total_price(self, obj):
        return f"₱ {intcomma(f'{obj.total_price:.2f}')}"
    get_formatted_total_price.short_description = 'Total Price'

    def user_full_name_display(self, obj):
        full_name = obj.user.get_full_name() or obj.user.username
        return f"{full_name} ({obj.user.email})"
    user_full_name_display.short_description = 'User'   

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'quantity', 'added_at', 'formatted_total_price')

    def formatted_total_price(self, obj):
        return intcomma(obj.total_price())  # Format total price with commas
    formatted_total_price.short_description = 'Total Price'


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
