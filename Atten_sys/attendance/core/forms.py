from django import forms
from .models import Attendance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['clock_in', 'clock_out', 'is_overtime']  # These are the editable fields
