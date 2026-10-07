from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "company", "role", "application_date", "status"]
    search_fields = ["company", "role"]
    list_filter = ["status"]
