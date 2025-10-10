from django.shortcuts import render
from django.http import HttpResponse
from analysis.utils import (
    get_coords_from_location, get_weather_data, 
    get_elevation_data, get_real_ndvi, get_ai_analysis
)
from archive.models import ReportSnapshot

def get_risk_color(score):
    if score <= 3:
        return '#7cb342'
    elif score <= 6:
        return '#FFA726'
    else:
        return '#EF5350'

def live_report(request):
    if request.method == 'POST':
        location = request.POST.get('location', '')
        country = request.POST.get('country', '')
        
        if not location or not country:
            return HttpResponse(
                '<div class="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-xl text-center">'
                '<i class="bi bi-exclamation-circle text-2xl mr-2"></i>'
                'Please provide both location and country to analyze.'
                '</div>',
                status=400
            )
        
        full_location = f"{location}, {country}" if country else location
        coords = get_coords_from_location(full_location)
        
        if not coords or coords.get('lat') == 6.5244:
            return HttpResponse(
                '<div class="bg-amber-100 border border-amber-400 text-amber-800 px-6 py-4 rounded-xl text-center">'
                '<i class="bi bi-search text-2xl mr-2"></i>'
                'Location not found. Please check the spelling and try again, or try a nearby major city.'
                '</div>',
                status=404
            )
        
        weather = get_weather_data(coords['lat'], coords['lon'])
        elevation = get_elevation_data(coords['lat'], coords['lon'])
        ndvi = get_real_ndvi(coords['lat'], coords['lon'])
        
        raw_data = {
            'precipitation_forecast': weather['precipitation_forecast'],
            'recent_rain': weather['recent_rain_trend'],
            'elevation': elevation,
            'ndvi': ndvi
        }
        
        flood_risk = min(10, int((weather['precipitation_forecast'] / 10) + (1 if elevation < 50 else 0)))
        air_quality = max(1, min(10, 10 - int(weather['precipitation_forecast'] / 15)))
        
        ai_result = get_ai_analysis(location, coords['country'], raw_data)
        land_health = ai_result.get('inferred_land_health_score', 6)
        analysis = ai_result.get('professional_analysis', {})
        
        risk_scores = {
            'flood': flood_risk,
            'air': air_quality,
            'land_health': land_health
        }
        
        analysis_text = f"""
        <div class="space-y-6">
            <div>
                <h3 class="text-2xl font-bold text-navy mb-4">{analysis.get('title', '')}</h3>
                <p class="text-sm text-gray-600 mb-2">{analysis.get('timestamp', '')}</p>
                <p class="text-md font-semibold text-gray-800 mb-4">{analysis.get('subject', '')}</p>
            </div>
            <div>
                <h4 class="font-bold text-lg text-navy mb-2">Risk Assessment</h4>
                <p class="text-gray-700 leading-relaxed">{analysis.get('assessment', '')}</p>
            </div>
            <div>
                <h4 class="font-bold text-lg text-navy mb-2">SDG 15 Compliance Analysis</h4>
                <p class="text-gray-700 leading-relaxed">{analysis.get('sdg_15_compliance', '')}</p>
            </div>
            <div>
                <h4 class="font-bold text-lg text-navy mb-2">Recommendations</h4>
                <p class="text-gray-700 leading-relaxed">{analysis.get('recommendations', '')}</p>
            </div>
        </div>
        """
        
        snapshot = ReportSnapshot.objects.create(
            location_name=location,
            country=coords['country'],
            latitude=coords['lat'],
            longitude=coords['lon'],
            risk_scores=risk_scores,
            ai_analysis_text=analysis_text,
            raw_data=raw_data
        )
        
        context = {
            'location_name': location,
            'country': coords['country'],
            'latitude': coords['lat'],
            'longitude': coords['lon'],
            'location_slug': snapshot.slug,
            'flood_risk': flood_risk,
            'air_quality': air_quality,
            'land_health': land_health,
            'flood_color': get_risk_color(flood_risk),
            'air_color': get_risk_color(air_quality),
            'land_color': get_risk_color(land_health),
            'analysis': analysis,
            'timestamp': analysis.get('timestamp', '')
        }
        
        return render(request, 'analysis/live_report.html', context)
    
    return HttpResponse('Method not allowed', status=405)
