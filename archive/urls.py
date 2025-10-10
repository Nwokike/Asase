from django.urls import path
from . import views

app_name = 'archive'

urlpatterns = [
    path('location/<slug:location_slug>/', views.location_hub, name='location_hub'),
    path('<slug:slug>/', views.snapshot_archive, name='snapshot'),
]
