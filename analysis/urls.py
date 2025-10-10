from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('live-report/', views.live_report, name='live_report'),
]
