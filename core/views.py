from django.shortcuts import render
from core.african_countries import AFRICAN_COUNTRIES

def search(request):
    context = {
        'african_countries': AFRICAN_COUNTRIES
    }
    return render(request, 'core/search.html', context)

def map_view(request):
    return render(request, 'core/map.html')

def about(request):
    return render(request, 'core/about.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')
