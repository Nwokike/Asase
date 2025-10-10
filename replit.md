# ASASE - Environmental Intelligence Platform

## Overview

ASASE (Earth Intelligence) is a Django-based environmental intelligence platform that provides real-time, AI-driven environmental risk analysis for African communities. The system analyzes three critical environmental factors: flood risk, air quality, and land health, with a focus on SDG 15 (Life on Land). The platform combines live environmental data from multiple sources with AI analysis to generate comprehensive risk assessments and maintains a historical archive of reports for trend analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Major Updates (October 2025)

### UI/UX Complete Redesign
- **Minimalist Glassmorphism Design**: Clean, beautiful aesthetic with glassmorphism applied to navigation, cards, and all UI elements
- **Icon-First Design**: Large, prominent icons (text-2xl to text-5xl) with proper positioning throughout the app
- **Enhanced Search Form**: Two-input design with location text field + dropdown of all 54 African countries
- **Radial Progress Bar**: Beautiful SVG circular progress visualization for Land Health Score
- **Better Typography**: Generous spacing, larger fonts (text-base to text-xl), and cleaner layout for premium feel

### Backend Performance & Caching Upgrade
- **Django Cache Framework**: Replaced `@lru_cache` with Django's cache framework for better control
  - Geocoding: 12-hour cache (coordinates don't change)
  - Weather: 30-minute cache (balance freshness vs API limits)
  - Elevation & NDVI: 12-hour cache (slow-changing terrain data)
- **Better Error Handling**: User-friendly error messages for invalid locations and missing inputs

### New Features
- **African Countries**: Complete list of 54 countries in search dropdown
- **Historical Trends**: Track Land Health scores over time for each location
- **Improved Validation**: Clear error feedback with helpful suggestions

## System Architecture

### Application Structure

**Problem**: Need to organize environmental analysis features into logical, maintainable modules while supporting both real-time analysis and historical data access.

**Solution**: Django's app-based architecture with three specialized apps:
- **core**: Handles the main user interface, search functionality, and static informational pages
- **analysis**: Performs live environmental risk calculations and AI-powered analysis using external APIs
- **archive**: Manages historical report storage, location-based data hubs, and trend visualization

**Rationale**: This separation follows Django's "apps should do one thing well" principle, making the codebase maintainable and allowing each concern to evolve independently. The modular structure also facilitates potential future extraction of services.

### Frontend Architecture

**Problem**: Need a modern, responsive UI with dynamic interactions while avoiding complex JavaScript build toolchains. Must be simple yet extremely beautiful with prominent, well-positioned icons.

**Solution**: Server-side rendered Django templates enhanced with HTMX for progressive enhancement, Tailwind CSS via CDN for styling, and glassmorphism design language for modern aesthetics.

**Rationale**: 
- **HTMX** enables dynamic content updates (form submissions, live reports) without page reloads while keeping logic server-side
- **Tailwind CDN** provides rapid styling without build steps, ideal for a Django project
- **Glassmorphism** (bg-white/10, backdrop-blur-lg, border-white/20) creates a premium modern feel aligned with environmental themes
- **Icon-First Design** with Bootstrap Icons at large sizes (text-2xl to text-5xl) for visual impact
- **Progressive enhancement** ensures core functionality works even if JavaScript fails

**Key UI Patterns**:
- Two-input search interface (location text field + African country dropdown with all 54 countries)
- Radial SVG progress bars for land health visualization (w-36 h-36 with animated stroke)
- Card-based layout with generous spacing (p-8 to p-12, gap-8 to gap-12)
- Large, well-positioned icons (text-2xl to text-5xl) using Bootstrap Icons with flexbox alignment
- Clean typography with font weights from light to bold (text-base to text-5xl)

### Data Flow & Caching Strategy

**Problem**: External API calls (geocoding, weather, satellite data) are expensive and slow; need to balance freshness with performance.

**Solution**: Django's cache framework with differentiated timeout strategies based on data volatility:
- **Geocoding**: 12 hours (43200s) - location coordinates rarely change
- **Weather data**: 30 minutes (1800s) - balance between freshness and API limits  
- **Elevation & NDVI**: 12 hours (43200s) - terrain and vegetation change slowly

**Implementation**:
```python
from django.core.cache import cache

def get_coords_from_location(location_name: str) -> dict:
    cache_key = f"geocode_{location_name}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    # ... fetch data
    cache.set(cache_key, result, timeout=43200)
    return result
```

**Rationale**: Upgraded from Python's `@lru_cache` (process-local, doesn't persist) to Django's cache framework which:
- Supports multiple backends (LocMemCache, Redis, Memcached)
- Shares cache across requests and processes
- Provides granular control over timeout values
- Enables production-ready caching strategies

Timeout values reflect the natural update frequency of each data type.

### AI Analysis Integration

**Problem**: Need to synthesize multiple environmental data sources into actionable insights for non-technical users.

**Solution**: Google Gemini AI integration that receives structured environmental data (precipitation, NDVI, elevation, air quality indicators) and generates human-readable risk assessments.

**Architecture**:
- Raw environmental data collected from APIs
- Data normalized into risk scores (0-10 scale)
- Structured prompt sent to Gemini with environmental context
- AI response parsed and displayed alongside quantitative metrics

**Rationale**: AI acts as an interpretation layer, translating technical metrics into community-relevant insights while maintaining transparency by showing both raw scores and analysis.

### Report Archival System

**Problem**: Users need to track environmental changes over time and compare historical conditions.

**Solution**: Django model `ReportSnapshot` that stores complete report state including:
- Location metadata (name, country, coordinates)
- Risk scores (flood, air quality, land health) as JSON
- Raw environmental data as JSON
- AI analysis text
- Auto-generated slug for URLs

**Key Features**:
- Location hub view aggregates all reports for a specific location
- Historical trend tracking for land health scores
- Timestamped snapshots enable temporal analysis
- Filterable archive interface (by location/country)

**Rationale**: JSON fields provide schema flexibility for evolving data structures while maintaining queryability for core metadata. Slugs create shareable, meaningful URLs. The archive serves as both a historical record and data source for trend analysis.

### Geographic & Mapping Components

**Problem**: Environmental data is inherently spatial; users need to visualize and interact with location-based information.

**Solution**: Leaflet.js maps integrated into multiple views:
- Interactive search on map page (click-to-analyze)
- Embedded maps in reports showing analysis location
- OpenStreetMap tiles for base layer

**Rationale**: Leaflet is lightweight, well-documented, and doesn't require API keys. OpenStreetMap aligns with the platform's open-data philosophy.

## External Dependencies

### Third-Party APIs

**OpenStreetMap Nominatim** (Geocoding)
- Converts location names to coordinates
- No API key required, rate-limited
- Fallback to sample data for Nigeria if geocoding fails

**OpenWeatherMap** (Weather Data)
- Provides precipitation forecasts and recent rainfall trends
- Used for flood risk calculation
- 30-minute cache timeout

**NASA/Sentinel Hub** (Satellite Imagery)
- NDVI (Normalized Difference Vegetation Index) for land health assessment
- Elevation data for terrain analysis
- 12-hour cache timeout due to slow-changing nature

**Google Gemini AI** (Analysis Generation)
- Requires `GEMINI_API_KEY` environment variable
- Synthesizes environmental data into human-readable reports
- Client initialized via `google.genai` SDK

### Frontend Libraries (CDN)

- **Tailwind CSS**: Utility-first styling framework
- **Bootstrap Icons**: Icon library (bi-* classes)
- **HTMX**: Dynamic HTML updates without JavaScript
- **Leaflet.js**: Interactive mapping
- **Google Fonts (Inter)**: Typography

### Python Packages

- **Django 5.2.7**: Web framework
- **python-dotenv**: Environment variable management
- **requests**: HTTP client for API calls
- **google-genai**: Google Gemini AI SDK

### Database

Currently using Django's default SQLite for development. The `ReportSnapshot` model uses:
- Standard Django fields for metadata
- JSONField for flexible data storage (risk_scores, raw_data)
- No complex relationships, making it portable to other databases

**Note**: The application is ready to migrate to PostgreSQL for production by updating `DATABASES` in settings.py. JSON fields work natively with PostgreSQL's jsonb type.

### Static Assets & PWA

- Service worker for offline capability
- Web manifest for installable PWA
- Custom CSS in `static/css/main.css` for utility classes and animations
- Logo assets in `static/images/`

### Environment Variables Required

- `GEMINI_API_KEY`: Google Gemini AI authentication
- `SECRET_KEY`: Django security key (currently hardcoded, should be moved to env)
- `DEBUG`: Development mode flag