# ASASE - Environmental Intelligence Platform

## Overview

ASASE (Earth Intelligence) is a Django-based environmental intelligence platform that provides real-time, AI-powered environmental risk analysis for African communities. The platform focuses on three key environmental metrics: flood risk, air quality, and land health, aligned with UN SDG 15: Life on Land.

The system generates environmental reports by synthesizing data from multiple external APIs (weather, satellite imagery, elevation) and using Google Gemini AI to produce comprehensive risk assessments. Reports can be viewed in real-time or accessed from a historical archive.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

The project follows Django's modular app pattern with three core Django apps:

1. **core** - Handles UI, static pages, and search interface
2. **analysis** - Manages real-time environmental analysis and report generation
3. **archive** - Stores and displays historical environmental reports

### Frontend Architecture

**Template Engine**: Django Templates with server-side rendering  
**UI Framework**: Tailwind CSS (via CDN) for styling  
**Interactivity**: HTMX for dynamic content loading without full page reloads  
**Mapping**: Leaflet.js for interactive map visualization  
**PWA Support**: Service workers and manifest files enable offline functionality and app installation

The frontend uses a hybrid approach - primarily server-rendered templates with HTMX for seamless partial page updates, avoiding the complexity of a separate JavaScript framework while maintaining modern interactivity.

### Backend Architecture

**Framework**: Django 5.2.7  
**Data Processing**: Server-side Python with synchronous request handling  
**Caching Strategy**: Django's built-in cache framework to reduce API calls and improve response times  
**AI Integration**: Google Gemini API for synthesizing environmental data into human-readable risk assessments

Key architectural decisions:
- Synchronous processing was chosen over async for simplicity, as analysis requests can take 20-30 seconds regardless
- Geocoding results are cached for 12 hours to minimize repeated API calls
- Environmental reports are permanently stored as ReportSnapshot models for historical analysis

### Database Design

**Primary Database**: PostgreSQL (configured via `dj-database-url`)  
**ORM**: Django ORM

**Core Model**: `ReportSnapshot` (archive/models.py)
- Stores complete environmental reports including location data, risk scores (JSON), AI analysis text, and raw sensor data
- Uses auto-generated slugs for URL-friendly access
- Ordered by timestamp (newest first) for archive browsing

The schema stores risk scores and raw environmental data as JSON fields, providing flexibility for varying data structures while maintaining queryable metadata (location, timestamp, coordinates).

### Data Flow Architecture

1. User submits location via search form (core app)
2. Request sent via HTMX to analysis endpoint
3. Geocoding converts location name to coordinates (cached)
4. Parallel data collection from external APIs (weather, elevation, NDVI satellite data)
5. Google Gemini synthesizes raw data into risk scores and narrative analysis
6. Report rendered and returned as HTML partial (HTMX swap)
7. ReportSnapshot created and saved to archive database

### External Dependencies

**AI & Analysis**:
- Google Gemini (google-generativeai) - AI synthesis of environmental data into risk assessments and recommendations

**Geospatial Data**:
- OpenStreetMap Nominatim API - Geocoding service to convert location names to coordinates
- OpenWeatherMap API - Weather data including precipitation forecasts
- Open-Meteo API - Elevation/terrain data
- NASA GIBS / Sentinel Hub - NDVI (Normalized Difference Vegetation Index) satellite imagery for land health analysis

**Infrastructure**:
- PostgreSQL - Primary relational database
- Render - Deployment platform (based on live demo URL)
- WhiteNoise - Static file serving in production

**Python Dependencies**:
- Django 5.2.7 - Web framework
- psycopg2-binary - PostgreSQL adapter
- requests - HTTP client for external API calls
- python-dotenv - Environment variable management
- gunicorn - Production WSGI server

### Deployment Configuration

The application is configured for cloud deployment with:
- Environment-based settings (DEBUG, SECRET_KEY, database URLs)
- CSRF trusted origins for Replit and Render domains
- Static file collection via Django's collectstatic
- Database configuration via dj-database-url for Heroku-style DATABASE_URL

### Performance Optimizations

**Caching**: Geocoding results cached to avoid repeated API calls for common locations  
**Static Assets**: Served via WhiteNoise in production, eliminating need for separate CDN  
**API Rate Limiting**: Caching reduces external API calls, lowering costs and improving response times

### Security Considerations

- CSRF protection enabled with trusted origins for deployment platforms
- Environment variables for sensitive API keys
- Allowed hosts configured for production domains
- User input sanitized through Django's template system