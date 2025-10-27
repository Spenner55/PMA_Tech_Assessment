# PMA Tech Assessment

A full-stack weather application built for the PM Accelerator Technical Assessment.  
It showcases a modern React + FastAPI architecture with Dockerized PostgreSQL.

---

## Features

- Search weather by **city, town, ZIP/postal code**, or coordinates  
- View **current weather** or a **5-day forecast**  
- Save, view, and delete queries from the database  
- Export weather data as CSV  
- Uses **Geoapify API** (for geocoding) and **Open-Meteo API** (for real weather data)  
- Includes developer info and an **Info** button linking to PM Accelerator

---

## Tech Stack

| Layer | Technology |
|-------|-------------|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI (Python), SQLAlchemy |
| Database | PostgreSQL (Dockerized) |
| APIs | Geoapify (Geocoding), Open-Meteo (Weather) |
| Dev Tools | Docker Compose, HTTPX, CORS Middleware |

---

## Setup & Run

### 1️ Clone the Repository
```bash
git clone https://github.com/Spenner55/PMA_Tech_Assessment.git
cd PMA_Tech_Assessment
```

### 2️ Add Environment Variables
Create a `.env` file with:
```bash
# Database
POSTGRES_USER=weather
POSTGRES_PASSWORD=weatherpw
POSTGRES_DB=weatherdb
DB_HOST=db
DB_PORT=5432

# Geoapify API Key (https://www.geoapify.com/)
GEOAPIFY_API_KEY=your_api_key_here
```

### 3 Run with Docker
```bash
docker compose up --build
```

Frontend → **http://localhost:5173**  
Backend → **http://localhost:8000**

---

## Usage

1. Enter a location (e.g., *Calgary*, *90210*, or *51.0447,-114.0719*)  
2. Click **Current** or **5-Day** to view data  
3. Click **Save to DB** to store results  
4. Click any saved record to view stored daily data  
5. Use **Export CSV** to download stored weather data  
6. Click the **Info** button for PM Accelerator details

---

## Project Structure

```
PMA_Tech_Assessment/
|── backend/
│   |── app/
│   │   |── main.py
│   │   |── db.py
│   │   |── models.py
│   │   |── schemas.py
│   │   |── services/
│   │       |── geocode.py
│   │       |── weather.py
│   |── Dockerfile
|── frontend/
│   |── src/
│   │   |── App.tsx
│   |── vite.config.ts
|── docker-compose.yml
|── .env
```

---

## API Overview

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/current?location=` | GET | Get current weather for a location |
| `/api/forecast5?location=` | GET | Get 5-day forecast |
| `/api/queries` | POST | Save a new query |
| `/api/queries` | GET | List saved queries |
| `/api/queries/{id}` | GET | Retrieve a specific query |
| `/api/queries/{id}` | DELETE | Delete a query |
| `/api/export?fmt=csv` | GET | Export all queries as CSV |

---

## Developer Info

**Created by:** [Dylan Windsor](https://www.linkedin.com/in/dylan-windsor-13526a262/)  
**For:** [PM Accelerator](https://www.linkedin.com/company/product-manager-accelerator)  
PM Accelerator is a global community and training platform helping aspiring professionals break into product management and tech.

---

## License

MIT License © 2025 Dylan Windsor
