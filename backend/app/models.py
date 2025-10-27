# backend/app/models.py
from __future__ import annotations

from datetime import datetime, date  # <-- Python types for annotations
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base

class WeatherQuery(Base):
    __tablename__ = "weather_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_location: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    # Use Python types in Mapped[...] and SQLAlchemy types in mapped_column(...)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None]   = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    records: Mapped[list["DailyWeather"]] = relationship(
        back_populates="query",
        cascade="all, delete-orphan"
    )

class DailyWeather(Base):
    __tablename__ = "daily_weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(
        ForeignKey("weather_queries.id", ondelete="CASCADE"),
        index=True
    )

    date: Mapped[date] = mapped_column(Date)  # Python type here
    temp_min_c: Mapped[float] = mapped_column(Float)
    temp_max_c: Mapped[float] = mapped_column(Float)

    query: Mapped[WeatherQuery] = relationship(back_populates="records")

    __table_args__ = (UniqueConstraint("query_id", "date", name="uq_query_date"),)
