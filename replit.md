# ASASE - Environmental Intelligence Platform

## Overview

ASASE (Earth Intelligence) is a Django-based environmental intelligence platform that provides real-time, AI-powered environmental risk analysis for African communities. The platform synthesizes data from multiple sources including satellite imagery, weather APIs, and terrain data to generate comprehensive environmental risk assessments focused on flood risk, air quality, and land health. The system aligns with UN Sustainable Development Goal 15: Life on Land.

The platform features a Progressive Web App (PWA) interface with offline capabilities, an interactive map-based search system, and an archive of historical environmental reports. It uses Google Gemini AI to synthesize environmental data into actionable insights for communities, policymakers, and researchers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

**Framework**: Django 5.2.7 with PostgreSQL database

**Application Structure**:
- **core**: Handles UI routing, static pages (search, about, privacy), and provides the main user interface templates
- **analysis**: Manages real-time environmental analysis, API integrations, and AI-powered report generation
- **archive**: Stores and retrieves historical environmental reports with location-based organization

**Data Processing Pipeline**:
1. User submits location (city/town + country)
2. Geocoding via OpenStreetMap Nominatim API converts location to coordinates
3. Parallel data fetching from multiple environmental APIs
4. Data synthesis using Google Gemini AI
5. Risk scoring algorithm generates 1-10 scores for flood, air quality, and land health
6. Report storage in PostgreSQL with slug-based URLs for archival access

**Caching Strategy**: Django's cache framework stores geocoding results (12-hour TTL) to reduce API calls and improve response times. This is critical for cost optimization given the reliance on external APIs.

**Database Schema**: Single model `ReportSnapshot` stores comprehensive environmental reports with JSONField for flexible data storage of risk scores and raw environmental data. Uses auto-generated slugs for URL-friendly archive access.

### Frontend Architecture

**Template System**: Django templates with server-side rendering
- Base template provides consistent navigation and PWA metadata
- Component-based templates for reusable UI elements (risk cards, maps)

**UI Framework**: Tailwind CSS for responsive design with custom color scheme (navy primary, green-leaf accent)

**Interactive Features**:
- **HTMX**: Enables dynamic form submission and partial page updates without full page reloads
- **Leaflet.js**: Interactive map interface for location visualization and click-to-analyze functionality
- **Bootstrap Icons**: Consistent iconography throughout the interface

**Progressive Web App**:
- Service worker for offline functionality
- Manifest file for installability on mobile devices
- Caching strategy for static assets and core functionality

### Data Scoring & AI Analysis

**Environmental Risk Scoring**: Custom algorithm processes raw environmental data to generate 1-10 risk scores:
- Flood risk: Based on precipitation forecasts, recent rainfall trends, and terrain elevation
- Air quality: Derived from atmospheric conditions and pollution indicators
- Land health: NDVI (Normalized Difference Vegetation Index) satellite data analysis

**AI Synthesis**: Google Gemini processes structured environmental data to generate human-readable analysis reports explaining risks, trends, and recommendations in context-appropriate language.

### Archive System

**Location Hubs**: Aggregates all reports for specific locations, showing historical trends and latest environmental status. Implements case-insensitive duplicate prevention to ensure unique location entries.

**Report Snapshots**: Timestamped environmental assessments stored with full context including coordinates, raw data, AI analysis, and computed risk scores. Accessible via unique slugs for sharing and reference.

## External Dependencies

### Third-Party APIs

**OpenStreetMap Nominatim**: Geocoding service to convert location names to geographic coordinates. Requires User-Agent header for compliance. Cached to reduce API load.

**OpenWeatherMap API**: Provides weather data including precipitation forecasts and recent rainfall patterns. Requires API key (OPENWEATHER_API_KEY environment variable).

**Open-Meteo**: Elevation data API for terrain analysis in flood risk assessment. No API key required.

**NASA GIBS / Sentinel Hub**: Satellite imagery services for NDVI (vegetation index) data. Used to assess land health and environmental degradation.

**Google Gemini AI**: Generative AI service for synthesizing environmental data into human-readable analysis reports. Requires API key (GEMINI_API_KEY environment variable).

### Python Dependencies

- **Django 5.2.7**: Web framework
- **psycopg2-binary**: PostgreSQL database adapter
- **google-generativeai**: Google Gemini AI client library
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management
- **dj-database-url**: Database configuration from environment
- **gunicorn**: Production WSGI server
- **whitenoise**: Static file serving for production

### Infrastructure Services

**Database**: PostgreSQL for production (configured via dj-database-url). Database stores environmental report snapshots with JSON fields for flexible data structure.

**Static Files**: WhiteNoise middleware serves static files in production without requiring separate CDN or static file server.

**Deployment**: Configured for deployment on Render.com with Replit.dev development support. CSRF trusted origins include both platforms.

### Frontend Libraries (CDN-delivered)

- Tailwind CSS (v3.x) for styling
- HTMX (v1.9.10) for dynamic interactions
- Leaflet.js (v1.9.4) for mapping
- Bootstrap Icons (v1.11.1) for iconography
- Inter font family (Google Fonts) for typography