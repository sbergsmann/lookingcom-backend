"""Pydantic schemas for room availability requests and responses"""

from datetime import date
from pydantic import BaseModel, Field, field_validator


class ChildRequest(BaseModel):
    """Child information for room search"""
    age: int = Field(..., ge=1, le=17, description="Child age in years (1-17)")


class RoomRequest(BaseModel):
    """Room configuration for search"""
    adults: int = Field(..., ge=1, description="Number of adults")
    children: list[ChildRequest] = Field(default_factory=list, max_length=8)
    
    @field_validator("children")
    @classmethod
    def validate_children_count(cls, v):
        if len(v) > 8:
            raise ValueError("Maximum 8 children per room")
        return v


class RoomAvailabilityRequest(BaseModel):
    """Request model for room availability search"""
    language: int = Field(0, ge=0, le=1, description="0=German, 1=English")
    hotel_id: str = Field(..., description="CapCorn Hotel ID")
    arrival: date = Field(..., description="Arrival date")
    departure: date = Field(..., description="Departure date")
    rooms: list[RoomRequest] = Field(..., min_length=1, max_length=10)
    
    @field_validator("rooms")
    @classmethod
    def validate_rooms_count(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 rooms per search")
        return v
    
    @field_validator("departure")
    @classmethod
    def validate_departure_after_arrival(cls, v, info):
        if "arrival" in info.data and v <= info.data["arrival"]:
            raise ValueError("Departure date must be after arrival date")
        return v


class ChildResponse(BaseModel):
    """Child information in response"""
    age: int


class RoomOption(BaseModel):
    """Available room option"""
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


class RoomResponse(BaseModel):
    """Room search result"""
    arrival: date
    departure: date
    adults: int
    children: list[ChildResponse] = Field(default_factory=list)
    options: list[RoomOption] = Field(default_factory=list)


class MemberResponse(BaseModel):
    """Hotel member with available rooms"""
    hotel_id: str
    rooms: list[RoomResponse]


class RoomAvailabilityResponse(BaseModel):
    """Response model for room availability search"""
    members: list[MemberResponse]
