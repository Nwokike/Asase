# ASASE - Environmental Intelligence Platform

## Overview

ASASE (Earth Intelligence) is a Django-based environmental intelligence platform focused on providing real-time, AI-driven risk analysis for African communities. The platform analyzes three critical environmental factors: flood risk, air quality, and land health (aligned with UN SDG 15: Life on Land). Users can search for any location and receive comprehensive environmental assessments powered by satellite data, weather APIs, and Google Gemini AI analysis. The platform also maintains a historical archive of all generated reports, creating a public environmental intelligence database.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Problem**: Need to organize environmental analysis features into logical, maintainable modules
**Solution**: Django app-based architecture with three main apps (core, analysis, archive)
**Rationale**: Separates concerns between user interface (core), real-time analysis (analysis), and historical data (archive)

The project uses Django's app pattern:
- **core**: Handles homepage search interface and static pages (about, privacy)
- **analysis**: Performs live environmental risk calculations and AI-powered analysis
- **archive**: Manages historical report storage and location-based data hubs

### Frontend Architecture

**Problem**: Need modern, responsive UI without complex build processes
**Solution**: Server-rendered templates with HTMX for dynamic interactions, Tailwind CSS via CDN
**Rationale**: Eliminates build step complexity while providing modern SPA-like user experience

Key technologies:
- Django templates for server-side rendering
- HTMX for AJAX form submissions without page reloads
- Tailwind CSS for utility-first styling
- Leaflet.js for interactive maps
- Progressive Web App (PWA) support with service workers

### Data Processing Pipeline

**Problem**: Need to aggregate data from multiple environmental data sources into unified risk scores
**Solution**: Multi-stage data pipeline combining geocoding, weather, elevation, satellite imagery, and AI analysis
**Rationale**: Each data source provides unique environmental indicators that combine to create comprehensive risk assessment

Pipeline stages:
1. **Geocoding**: Convert location names to coordinates using OpenStreetMap Nominatim
2. **Weather Data**: Fetch precipitation forecasts and historical trends from OpenWeatherMap
3. **Elevation Data**: Retrieve terrain elevation from Open-Meteo API
4. **NDVI Analysis**: Get vegetation health data from NASA GIBS/Sentinel Hub satellites
5. **AI Synthesis**: Google Gemini 2.5 Flash analyzes all data to produce professional environmental reports
6. **Risk Scoring**: Calculate numerical risk scores (1-10 scale) for flood, air quality, and land health

### Caching Strategy

**Problem**: External API calls are expensive and slow
**Solution**: LRU caching with `@lru_cache` decorator on utility functions
**Rationale**: Frequently requested locations get instant responses, reduces API costs

The `get_coords_from_location` and `get_weather_data` functions use `@lru_cache(maxsize=100)` to cache results in memory.

### Data Persistence

**Problem**: Need to preserve historical environmental data for trend analysis and public archive
**Solution**: PostgreSQL-backed Django ORM with JSONField for flexible data storage
**Rationale**: Structured relational data for core fields, JSON flexibility for variable analysis results

**ReportSnapshot Model**:
- Stores location metadata (name, country, coordinates)
- JSONField for risk scores (allows schema evolution)
- TextField for formatted AI analysis
- JSONField for raw data from external APIs
- Auto-generated slugs for SEO-friendly URLs
- Timestamp-based ordering for chronological archives

### AI Integration

**Problem**: Raw environmental data needs expert interpretation for non-technical users
**Solution**: Google Gemini 2.5 Flash processes all data sources to generate professional environmental reports
**Rationale**: Large language models can synthesize multiple data streams into coherent, actionable insights aligned with SDG 15 compliance

The AI receives structured data about precipitation, elevation, NDVI, and location context, then produces formatted reports with risk assessments, SDG 15 compliance analysis, and actionable recommendations.

### URL Routing Architecture

**Problem**: Need clean, semantic URLs for both live reports and historical archives
**Solution**: Namespaced URL patterns with slug-based routing
**Rationale**: Enables SEO-friendly URLs and logical URL hierarchy

URL structure:
- `/` - Homepage search interface
- `/analysis/live-report/` - Real-time environmental analysis (POST)
- `/archive/<slug>/` - Individual historical report
- `/archive/location/<location_slug>/` - Location hub with all reports for specific location

### Progressive Web App Design

**Problem**: Users in areas with limited connectivity need offline access
**Solution**: Service worker caching and PWA manifest for installable app experience
**Rationale**: Makes platform accessible as standalone app with offline capabilities

PWA features:
- Service worker caches static assets
- Manifest.json enables "Add to Home Screen"
- Offline fallback for previously viewed content

## External Dependencies

### Third-Party APIs

1. **OpenStreetMap Nominatim** (Geocoding)
   - Purpose: Convert location names to latitude/longitude coordinates
   - No API key required
   - Rate-limited, requires User-Agent header

2. **OpenWeatherMap One Call API** (Weather Data)
   - Purpose: Real-time precipitation forecasts and weather trends
   - Requires: `OPENWEATHER_API_KEY` environment variable
   - Provides: Precipitation forecasts, temperature, humidity

3. **Open-Meteo** (Elevation Data)
   - Purpose: Terrain elevation for flood risk assessment
   - No API key required
   - Returns elevation in meters above sea level

4. **NASA GIBS / Sentinel Hub** (Satellite Imagery)
   - Purpose: NDVI (Normalized Difference Vegetation Index) for land health
   - Used to assess vegetation cover and ecosystem health
   - Aligns with SDG 15 (Life on Land) metrics

5. **Google Gemini 2.5 Flash** (AI Analysis)
   - Purpose: Synthesize all environmental data into professional reports
   - Requires: `GEMINI_API_KEY` environment variable
   - Generates structured analysis with SDG 15 compliance assessment

### Database

**PostgreSQL** (via Django ORM)
- Primary data store for ReportSnapshot model
- JSONField support for flexible schema (requires PostgreSQL 9.4+)
- Default Django migrations handle schema management

Note: The application uses Django's ORM layer, allowing flexibility to use SQLite for development or other database backends, though PostgreSQL is recommended for production due to JSONField support.

### Frontend Libraries (CDN)

- **Tailwind CSS** - Utility-first styling framework
- **HTMX** - Dynamic HTML interactions without JavaScript
- **Leaflet.js** - Interactive map rendering
- **Google Fonts (Inter)** - Typography

### Python Dependencies

- **Django 5.2.7** - Web framework
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for external APIs
- **google-generativeai** - Google Gemini SDK

### Environment Variables Required

```
GEMINI_API_KEY=<Google Gemini API key>
OPENWEATHER_API_KEY=<OpenWeatherMap API key>
SECRET_KEY=<Django secret key>
DEBUG=<True/False>
```
