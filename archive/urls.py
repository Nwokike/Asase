from django.urls import path
from . import views

app_name = 'archive'

urlpatterns = [
    path('all/', views.archive_main, name='archive_main'),
    path('<slug:slug>/', views.snapshot_archive, name='snapshot'),
]
