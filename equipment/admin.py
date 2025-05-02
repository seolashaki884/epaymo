from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at')
    search_fields = ['name']
    list_filter = ['status']
