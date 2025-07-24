from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_main, name='attendance_main'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('gps-live/', views.gps_live_view, name='gps_live_view'),
]
