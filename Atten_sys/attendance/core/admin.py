from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'clock_in', 'clock_out', 'is_overtime')
    list_filter = ('user', 'date', 'is_overtime')
    search_fields = ('user__username',)
