"""Pydantic schemas for reservation/booking requests"""

from datetime import date
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from enum import IntEnum


class MealPlan(IntEnum):
    """Meal plan options"""
    BREAKFAST = 1
    HALF_BOARD = 2
    FULL_BOARD = 3
    NO_MEALS = 4
    ALL_INCLUSIVE = 5


class GuestCount(BaseModel):
    """Guest count information"""
    age_qualifying_code: int = Field(..., description="10=Adults, 8=Children")
    count: int = Field(..., ge=1)
    age: Optional[int] = Field(None, ge=1, le=17, description="Required for children")


class ServiceRequest(BaseModel):
    """Additional service booking"""
    name: str = Field(..., description="Service name")
    quantity: int = Field(..., ge=1)
    amount_after_tax: float = Field(..., ge=0)


class AddressInfo(BaseModel):
    """Guest address information"""
    address_line: str
    city_name: str
    postal_code: str
    country_code: str = Field(..., min_length=2, max_length=2)


class GuestInfo(BaseModel):
    """Guest personal information"""
    name_prefix: str = Field(..., description="e.g., Herr, Frau")
    given_name: str
    surname: str
    phone_number: str
    email: EmailStr
    address: AddressInfo


class ReservationRequest(BaseModel):
    """Complete reservation/booking request"""
    hotel_id: str = Field(..., description="CapCorn Hotel ID")
    room_type_code: str = Field(..., max_length=8, description="Room category code")
    number_of_units: int = Field(1, ge=1, description="Number of rooms to book")
    meal_plan: MealPlan = Field(..., description="Included meals")
    guest_counts: list[GuestCount] = Field(..., min_length=1)
    arrival: date
    departure: date
    total_amount: float = Field(..., ge=0, description="Total price in EUR")
    guest: GuestInfo
    services: list[ServiceRequest] = Field(default_factory=list)
    booking_comment: Optional[str] = Field(None, max_length=200)
    reservation_id: str = Field(..., description="Unique booking ID in your system")
    source: str = Field("Hackathon", description="Source/channel name")
    
    @field_validator("departure")
    @classmethod
    def validate_departure_after_arrival(cls, v, info):
        if "arrival" in info.data and v <= info.data["arrival"]:
            raise ValueError("Departure date must be after arrival date")
        return v


class ReservationResponse(BaseModel):
    """Response from reservation attempt"""
    success: bool
    message: str
    reservation_id: Optional[str] = None
    errors: Optional[list[str]] = None
