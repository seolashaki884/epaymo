from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_tag', 'category', 'status', 'created_at')
    search_fields = ('name', 'asset_tag', 'category')
    list_filter = ('status', 'category')
