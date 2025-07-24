from django.db import models
from django.contrib.auth.models import User

class Attendance(models.Model):
    """
    Stores individual attendance records for employees.
    Each entry corresponds to a single day with optional
    GPS proof and overtime calculation.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attendances",
        help_text="User who is marking attendance"
    )
    date = models.DateField(
        auto_now_add=True,
        help_text="Date of attendance (auto-filled)"
    )
    clock_in = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when the user clocked in"
    )
    clock_out = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when the user clocked out"
    )
    is_overtime = models.BooleanField(
        default=False,
        help_text="Indicates whether the employee worked overtime"
    )
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    is_overtime = models.BooleanField(default=False)
    break_violation = models.BooleanField(default=False) 

    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

