from django.shortcuts import render

def search(request):
    return render(request, 'core/search.html')

def map_view(request):
    return render(request, 'core/map.html')

def about(request):
    return render(request, 'core/about.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')
