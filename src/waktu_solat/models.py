from pydantic import BaseModel
from typing import List

class PrayerTimes(BaseModel):
    date: str
    day: str
    imsak: str
    fajr: str
    syuruk: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str

class Zone(BaseModel):
    name: str
    code: str
    negeri: str
