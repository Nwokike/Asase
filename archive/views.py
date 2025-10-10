from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from archive.models import ReportSnapshot
from django.utils.text import slugify

def get_risk_color(score):
    if score <= 3:
        return '#7cb342'
    elif score <= 6:
        return '#FFA726'
    else:
        return '#EF5350'

def archive_main(request):
    reports = ReportSnapshot.objects.all()
    
    filter_location = request.GET.get('location', '')
    filter_country = request.GET.get('country', '')
    
    if filter_location:
        reports = reports.filter(location_name__icontains=filter_location)
    if filter_country:
        reports = reports.filter(country__icontains=filter_country)
    
    paginator = Paginator(reports, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reports': page_obj,
        'filter_location': filter_location,
        'filter_country': filter_country,
    }
    
    return render(request, 'archive/archive_main.html', context)

def location_hub(request, location_slug):
    snapshots = ReportSnapshot.objects.filter(
        slug__icontains=location_slug.split('-')[0]
    )
    
    if snapshots.exists():
        latest = snapshots.first()
        context = {
            'location_name': latest.location_name,
            'country': latest.country,
            'snapshots': snapshots,
            'live_data': latest.risk_scores,
            'flood_color': get_risk_color(latest.risk_scores.get('flood', 5)),
            'air_color': get_risk_color(latest.risk_scores.get('air', 5)),
            'land_color': get_risk_color(latest.risk_scores.get('land_health', 5)),
        }
        return render(request, 'archive/location_hub.html', context)
    
    return render(request, '404.html', status=404)

def snapshot_archive(request, slug):
    snapshot = get_object_or_404(ReportSnapshot, slug=slug)
    
    context = {
        'snapshot': snapshot,
        'flood_color': get_risk_color(snapshot.risk_scores.get('flood', 5)),
        'air_color': get_risk_color(snapshot.risk_scores.get('air', 5)),
        'land_color': get_risk_color(snapshot.risk_scores.get('land_health', 5)),
    }
    
    return render(request, 'archive/snapshot_archive.html', context)
