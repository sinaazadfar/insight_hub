from django.contrib import admin
from .models import PredefinedTask, Schedule, Execution

@admin.register(PredefinedTask)
class PTAdmin(admin.ModelAdmin):
    list_display = ("name","is_schedulable","created_at")
    search_fields = ("name",)

@admin.register(Schedule)
class SAdmin(admin.ModelAdmin):
    list_display = ("id","task","owner","status","cron_expression","created_at")
    list_filter = ("status","task","owner")

@admin.register(Execution)
class EAdmin(admin.ModelAdmin):
    list_display = ("id","schedule","status","started_at","finished_at")
    list_filter = ("status",)   
