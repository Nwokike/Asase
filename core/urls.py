from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('search/', views.search, name='search'),
    path('map/', views.map_view, name='map'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy_policy, name='privacy'),
]
