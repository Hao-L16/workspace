from django.contrib import admin
from .models import QuoteSearch
# Register your models here.

@admin.register(QuoteSearch)
class QuoteSearchAdmin(admin.ModelAdmin):
    list_display = ("id","user","pickup_entity_id","pickup_datetime","dropoff_datetime","driver_age","created_at")
    list_filter = ("pickup_entity_id","created_at")
    search_fields = ("pickup_entity_id",)
