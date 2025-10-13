# ASASE - Environmental Intelligence Platform

## Overview

ASASE (Earth Intelligence) is a Django-based environmental intelligence platform designed to provide real-time, AI-driven environmental risk analysis for African communities. The platform analyzes three critical environmental factors—flood risk, air quality, and land health—using satellite data, weather APIs, and Google's Gemini AI. The application focuses on supporting UN Sustainable Development Goal 15 (Life on Land) by tracking land degradation and ecosystem health across Africa.

The platform features a modern Progressive Web App (PWA) interface with glassmorphism design, interactive mapping capabilities, and an archive system for historical environmental data. Users can search for any location in Africa, receive comprehensive environmental risk assessments, and access historical trends for specific locations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- TailwindCSS for utility-first styling with custom configuration (navy blue and green-leaf color scheme)
- HTMX for dynamic content loading without full page refreshes
- Leaflet.js for interactive mapping functionality
- Bootstrap Icons for UI iconography
- Progressive Web App (PWA) with service worker for offline capability

**Design Patterns:**
- Glassmorphism aesthetic with backdrop-blur effects and semi-transparent white overlays
- Responsive mobile-first design with special attention to mobile navigation (z-index management for bottom navigation)
- Auto-scroll to results after analysis completion
- Visual and browser notifications for completed analyses
- Share functionality using Web Share API with clipboard fallback

**Key UI Components:**
- Two-input search interface (location text field + country dropdown for 54 African countries)
- Radial SVG progress visualization for Land Health Score
- Interactive map with click-to-analyze functionality
- Archive system with filtering and pagination
- Location Hub pages showing historical trends

### Backend Architecture

**Framework:** Django 5.2.7 with Python 3.11

**Application Structure:**
- `core`: Main landing pages (search, map view, about, privacy)
- `analysis`: Live environmental risk analysis logic
- `archive`: Historical report storage and retrieval
- `asase_project`: Project configuration and settings

**Data Flow Pattern:**
1. User submits location via HTMX-powered form
2. Backend geocodes location using OpenStreetMap Nominatim API
3. Parallel data collection from multiple APIs (weather, elevation, NDVI)
4. AI analysis via Google Gemini to generate risk scores and recommendations
5. Results stored in database as ReportSnapshot
6. Response rendered and returned to frontend via HTMX

**Caching Strategy:**
- Django's cache framework (replacing earlier @lru_cache implementation)
- Geocoding results: 12-hour cache timeout
- Weather data: 30-minute cache timeout  
- Elevation & NDVI data: 12-hour cache timeout
- Improves performance and reduces API calls

**Risk Scoring System:**
- Three risk categories: Flood Risk, Air Quality, Land Health
- Scores range from 1-10 with color coding:
  - 1-3: Green (#7cb342) - Low risk
  - 4-6: Orange (#FFA726) - Medium risk
  - 7-10: Red (#EF5350) - High risk

### Database Design

**Primary Model: ReportSnapshot**
- Stores complete environmental analysis results
- Fields: location_name, country, latitude, longitude, risk_scores (JSON), ai_analysis_text, raw_data (JSON), timestamp
- Auto-generated slug for URL routing (format: location-name-YYYY-MM-DD-HHMM)
- Ordered by timestamp descending for archive display

**Database Configuration:**
- Supports PostgreSQL via dj-database-url for production (Render deployment)
- SQLite for local development
- JSON fields for flexible storage of risk scores and raw environmental data

### External Dependencies

**AI & Analysis:**
- Google Gemini AI (google-generativeai==0.8.5): Generates environmental risk analysis and actionable recommendations
- Google GenAI (google-genai==1.42.0): Core AI client library

**Geospatial & Environmental APIs:**
- OpenStreetMap Nominatim: Geocoding service to convert location names to coordinates
- OpenWeatherMap: Current weather data and precipitation forecasts
- NASA/USGS Elevation API: Terrain elevation data for flood risk assessment
- Sentinel Hub / NASA NDVI: Normalized Difference Vegetation Index for land health tracking

**Infrastructure Services:**
- WhiteNoise (whitenoise==6.11.0): Static file serving for production
- Gunicorn (gunicorn==23.0.0): WSGI HTTP server for deployment
- psycopg2-binary (==2.9.11): PostgreSQL database adapter

**Deployment Platform:**
- Render.com: Cloud platform for web service and PostgreSQL hosting
- Configured via render.yaml blueprint for automated deployment
- Environment variables: GEMINI_API_KEY, SECRET_KEY, DEBUG, DATABASE_URL

**Additional Libraries:**
- python-dotenv: Environment variable management
- requests: HTTP client for API calls
- django-htmx integration for dynamic updates