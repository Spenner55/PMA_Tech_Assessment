from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, timedelta
import io, pandas as pd

from .db import Base, engine, get_db
from . import models, schemas
from .services.geocode import geocode_any, GeocodeError
from .services.weather import fetch_current, fetch_daily

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PMA Weather App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_range(start: date | None, end: date | None):
    if start and end and start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    if start and end is None:
        end = start
    if end and start is None:
        start = end
    return start, end

@app.get("/api/current", response_model=schemas.CurrentWeatherOut)
async def current_weather(location: str = Query(..., description="City, landmark, postal/zip, or 'lat,lon'")):
    try:
        lat, lon, _ = await geocode_any(location)
    except GeocodeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    cur = await fetch_current(lat, lon)
    if not cur:
        raise HTTPException(404, "No current weather found")
    return schemas.CurrentWeatherOut(
        temperature_c=cur.get("temperature"),
        windspeed_kph=cur.get("windspeed"),
        winddirection_deg=cur.get("winddirection"),
        description="Current conditions"
    )

@app.get("/api/forecast5")
async def forecast_5day(location: str):
    from datetime import date
    try:
        lat, lon, _ = await geocode_any(location)
    except GeocodeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    start = date.today()
    end = start + timedelta(days=4)
    return await fetch_daily(lat, lon, start, end)

@app.post("/api/queries", response_model=schemas.QueryOut, status_code=201)
async def create_query(payload: schemas.QueryCreate, db: Session = Depends(get_db)):
    start, end = validate_range(payload.start_date, payload.end_date)
    # Default to a 5-day window if nothing given
    if not start:
        start = date.today()
        end = start + timedelta(days=4)

    lat, lon, resolved = await geocode_any(payload.location)
    # persist query
    q = models.WeatherQuery(
        raw_location=resolved, latitude=lat, longitude=lon, start_date=start, end_date=end
    )
    db.add(q); db.flush()

    daily = await fetch_daily(lat, lon, start, end)
    days = daily.get("time", [])
    tmin = daily.get("temperature_2m_min", [])
    tmax = daily.get("temperature_2m_max", [])
    for i, d in enumerate(days):
        db.add(models.DailyWeather(
            query_id=q.id, date=date.fromisoformat(d),
            temp_min_c=float(tmin[i]), temp_max_c=float(tmax[i])
        ))
    db.commit(); db.refresh(q)
    return q

@app.get("/api/queries", response_model=list[schemas.QueryOut])
def list_queries(db: Session = Depends(get_db)):
    return db.query(models.WeatherQuery).order_by(models.WeatherQuery.id.desc()).all()

@app.get("/api/queries/{qid}", response_model=schemas.QueryOut)
def get_query(qid: int, db: Session = Depends(get_db)):
    q = db.get(models.WeatherQuery, qid)
    if not q: raise HTTPException(404, "Not found")
    return q

@app.put("/api/queries/{qid}", response_model=schemas.QueryOut)
async def update_query(qid: int, payload: schemas.QueryUpdate, db: Session = Depends(get_db)):
    q = db.get(models.WeatherQuery, qid)
    if not q: raise HTTPException(404, "Not found")

    start, end = validate_range(payload.start_date or q.start_date, payload.end_date or q.end_date)

    if payload.location:
        lat, lon, resolved = await geocode_any(payload.location)
        q.raw_location, q.latitude, q.longitude = resolved, lat, lon

    q.start_date, q.end_date = start, end
    # refresh stored daily data
    db.query(models.DailyWeather).filter(models.DailyWeather.query_id == q.id).delete()
    daily = await fetch_daily(q.latitude, q.longitude, start, end)
    for i, d in enumerate(daily.get("time", [])):
        db.add(models.DailyWeather(
            query_id=q.id, date=date.fromisoformat(d),
            temp_min_c=float(daily["temperature_2m_min"][i]),
            temp_max_c=float(daily["temperature_2m_max"][i]),
        ))
    db.commit(); db.refresh(q)
    return q

@app.delete("/api/queries/{qid}", status_code=204)
def delete_query(qid: int, db: Session = Depends(get_db)):
    q = db.get(models.WeatherQuery, qid)
    if not q: raise HTTPException(404, "Not found")
    db.delete(q); db.commit()
    return

# ---------- Optional: export ----------
@app.get("/api/export")
def export_data(fmt: str = Query("csv", enum=["csv", "json"]), db: Session = Depends(get_db)):
    rows = (
        db.query(models.WeatherQuery.id, models.WeatherQuery.raw_location,
                 models.WeatherQuery.latitude, models.WeatherQuery.longitude,
                 models.DailyWeather.date, models.DailyWeather.temp_min_c, models.DailyWeather.temp_max_c)
        .join(models.DailyWeather, models.DailyWeather.query_id == models.WeatherQuery.id)
        .order_by(models.WeatherQuery.id.desc(), models.DailyWeather.date.asc())
        .all()
    )
    df = pd.DataFrame(rows, columns=["query_id","location","lat","lon","date","tmin_c","tmax_c"])
    if fmt == "json":
        return df.to_dict(orient="records")
    # CSV
    buf = io.StringIO(); df.to_csv(buf, index=False)
    return {"csv": buf.getvalue()}
