from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime

class QueryCreate(BaseModel):
    location: str = Field(..., examples=["Calgary", "51.05,-114.07", "T2P 5C5"])
    start_date: date | None = None
    end_date: date | None = None

class QueryUpdate(BaseModel):
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None

class DailyWeatherOut(BaseModel):
    date: date
    temp_min_c: float
    temp_max_c: float
    model_config = ConfigDict(from_attributes=True)

class QueryOut(BaseModel):
    id: int
    raw_location: str
    latitude: float
    longitude: float
    start_date: date | None
    end_date: date | None
    created_at: datetime
    records: list[DailyWeatherOut]
    model_config = ConfigDict(from_attributes=True)

class CurrentWeatherOut(BaseModel):
    temperature_c: float
    windspeed_kph: float | None = None
    winddirection_deg: float | None = None
    description: str | None = None
