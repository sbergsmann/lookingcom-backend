"""Simplified request schemas for room availability"""

from datetime import date, timedelta
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Language(str, Enum):
    """Supported languages"""
    GERMAN = "de"
    ENGLISH = "en"


class ChildAgeRequest(BaseModel):
    """Child age information"""
    age: int = Field(..., ge=1, le=17, description="Child age in years (1-17)")


class TimeSpan(BaseModel):
    """Date range for search"""
    from_date: date = Field(..., alias="from", description="Start date of search period")
    to_date: date = Field(..., alias="to", description="End date of search period")
    
    @field_validator("to_date")
    @classmethod
    def validate_to_after_from(cls, v, info):
        if "from_date" in info.data and v <= info.data["from_date"]:
            raise ValueError("'to' date must be after 'from' date")
        return v
    
    class Config:
        populate_by_name = True


class SimplifiedRoomSearchRequest(BaseModel):
    """Simplified request model for room search with flexible duration"""
    language: Language = Field(Language.GERMAN, description="Language preference")
    timespan: TimeSpan = Field(..., description="Date range to search within")
    duration: int = Field(..., ge=1, description="Length of stay in days")
    adults: int = Field(..., ge=1, description="Number of adults")
    children: list[ChildAgeRequest] = Field(default_factory=list, max_length=8)
    
    @field_validator("children")
    @classmethod
    def validate_children_count(cls, v):
        if len(v) > 8:
            raise ValueError("Maximum 8 children per room")
        return v
    
    @field_validator("duration")
    @classmethod
    def validate_duration_within_timespan(cls, v, info):
        if "timespan" in info.data:
            timespan = info.data["timespan"]
            max_duration = (timespan.to_date - timespan.from_date).days
            if v > max_duration:
                raise ValueError(
                    f"Duration ({v} days) cannot exceed timespan ({max_duration} days)"
                )
        return v
    
    def generate_date_ranges(self) -> list[tuple[date, date]]:
        """
        Generate all possible date ranges for the given duration within timespan.
        
        Returns list of (arrival, departure) tuples.
        """
        date_ranges = []
        current_arrival = self.timespan.from_date
        max_arrival = self.timespan.to_date - timedelta(days=self.duration)
        
        while current_arrival <= max_arrival:
            departure = current_arrival + timedelta(days=self.duration)
            date_ranges.append((current_arrival, departure))
            current_arrival += timedelta(days=1)
        
        return date_ranges


class RoomOptionWithDateRange(BaseModel):
    """Room option with associated date range"""
    arrival: date
    departure: date
    catc: str = Field(..., description="Room category code")
    type: str = Field(..., description="General room name")
    description: str = Field(..., description="Detailed room description")
    size: int = Field(..., description="Room size in square meters")
    price: float = Field(..., description="Total price for the stay")
    price_per_person: float
    price_per_adult: float
    price_per_night: float
    board: int = Field(..., description="1=Breakfast, 2=Half board, 3=Full board, 4=No meals, 5=All inclusive")
    room_type: int = Field(..., description="1=Hotel room, 2=Apartment/Holiday home")


class SimplifiedRoomSearchResponse(BaseModel):
    """Response model with all room options across date ranges"""
    total_queries: int = Field(..., description="Number of date ranges searched")
    total_options: int = Field(..., description="Total number of room options found")
    duration_days: int = Field(..., description="Stay duration in days")
    options: list[RoomOptionWithDateRange] = Field(
        default_factory=list,
        description="All available room options across all date ranges"
    )
