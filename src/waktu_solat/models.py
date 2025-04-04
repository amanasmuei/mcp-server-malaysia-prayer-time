"""
Data models for prayer times and zones.

This module defines Pydantic models for representing prayer times and zone data
with built-in validation and helper methods.
"""

from datetime import datetime, time
from typing import List
from pydantic import BaseModel, Field, field_validator
import re


TIME_PATTERN = re.compile(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")


class PrayerTimes(BaseModel):
    """
    Represents prayer times for a specific date.

    Fields:
        date: Date in YYYY-MM-DD format
        day: Day of the week
        imsak: Pre-dawn meal time (HH:mm)
        fajr: Dawn prayer time (HH:mm)
        syuruk: Sunrise time (HH:mm)
        dhuhr: Noon prayer time (HH:mm)
        asr: Afternoon prayer time (HH:mm)
        maghrib: Sunset prayer time (HH:mm)
        isha: Night prayer time (HH:mm)
    """

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day: str = Field(..., description="Day of the week")
    imsak: str | None = Field(None, description="Pre-dawn meal time")
    fajr: str = Field(..., description="Dawn prayer time")
    syuruk: str = Field(..., description="Sunrise time")
    dhuhr: str = Field(..., description="Noon prayer time")
    asr: str = Field(..., description="Afternoon prayer time")
    maghrib: str = Field(..., description="Sunset prayer time")
    isha: str = Field(..., description="Night prayer time")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    @field_validator("imsak", "fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha")
    @classmethod
    def validate_time(cls, v: str | None) -> str | None:
        """Validate time format."""
        if v is None:
            return None
        if not TIME_PATTERN.match(v):
            raise ValueError("Invalid time format. Expected HH:mm")
        return v

    def get_time(self, prayer: str) -> time:
        """
        Get prayer time as datetime.time object.

        Args:
            prayer: Name of the prayer (e.g., 'fajr', 'dhuhr')

        Returns:
            datetime.time object representing the prayer time

        Raises:
            ValueError: If prayer name is invalid
        """
        if not hasattr(self, prayer.lower()):
            raise ValueError(f"Invalid prayer name: {prayer}")

        time_str = getattr(self, prayer.lower())
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)

    def is_valid_prayer_time(self, prayer: str) -> bool:
        """
        Check if a given string is a valid prayer name.

        Args:
            prayer: Name of the prayer to check

        Returns:
            True if valid prayer name, False otherwise
        """
        return prayer.lower() in {
            "imsak",
            "fajr",
            "syuruk",
            "dhuhr",
            "asr",
            "maghrib",
            "isha",
        }

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "date": "2024-04-04",
                "day": "Thursday",
                "imsak": "05:45",
                "fajr": "05:55",
                "syuruk": "07:08",
                "dhuhr": "13:16",
                "asr": "16:27",
                "maghrib": "19:21",
                "isha": "20:30",
            }
        }


class Zone(BaseModel):
    """
    Represents a prayer time zone.

    Fields:
        name: Name of the zone
        code: Unique zone code (e.g., 'SGR01')
        negeri: State name
    """

    name: str = Field(..., description="Name of the zone", min_length=1)
    code: str = Field(..., description="Unique zone code", min_length=1)
    negeri: str = Field(..., description="State name", min_length=1)

    @field_validator("name", "negeri", "code")
    @classmethod
    def validate_fields(cls, v: str) -> str:
        """Validate all string fields."""
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate zone code format."""
        if not re.match(r"^[A-Z]{3}\d{2}$", v):
            raise ValueError("Invalid zone code format. Expected format: ABC12")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {"name": "Gombak", "code": "SGR01", "negeri": "Selangor"}
        }
