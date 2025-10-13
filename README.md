# 🌍 ASASE – Environmental Intelligence Platform

**ASASE (Earth Intelligence)** is a Django-based platform providing real-time, AI-powered environmental risk analysis for African communities.  
It focuses on **flood risk**, **air quality**, and **land health**, aligned with **UN SDG 15: Life on Land**.

🔗 **Live Demo:** [asase-app.onrender.com](https://asase-app.onrender.com)

---

## 🚀 Key Features

- **AI Environmental Reports** – Synthesizes satellite, weather, and terrain data using Google Gemini.  
- **Real-Time Risk Analysis** – Generates instant environmental scores for any African location.  
- **Historical Archive** – Stores and displays past environmental reports.  
- **Progressive Web App (PWA)** – Installable and usable offline.  
- **Interactive Map Interface** – Built with Leaflet.js for intuitive visualization.  
- **Optimized Performance** – Caching reduces API costs and response times.  

---

## 🧠 Tech Stack

**Backend:** Django, PostgreSQL  
**Frontend:** Django Templates, Tailwind CSS, HTMX, Leaflet.js  
**AI & Data Sources:**  
- Google Gemini (AI synthesis)  
- OpenStreetMap (Geocoding)  
- OpenWeatherMap (Weather data)  
- Open-Meteo (Elevation data)  
- NASA GIBS / Sentinel Hub (NDVI satellite data)  

---

## ⚙️ Environment Variables

```bash
GEMINI_API_KEY=<Google Gemini API key>
OPENWEATHER_API_KEY=<OpenWeatherMap API key>
SECRET_KEY=<Django secret key>
DEBUG=<True/False>


---

🧩 Project Structure

asase_project/
├── core/        # UI, routing, and static pages
├── analysis/    # Real-time environmental analysis
├── archive/     # Historical reports and data storage
├── static/      # CSS, JS, images
├── templates/   # Django templates


---

🗄️ Database

PostgreSQL for production (supports JSONField for flexible storage)

SQLite for local development



---

💡 Development

# Clone repository
git clone https://github.com/Nwokike/Asase.git
cd Asase

# Install dependencies
pip install -r requirements.txt

# Run migrations and start server
python manage.py migrate
python manage.py runserver


---

🧭 License

MIT License © 2025 Nwokike
