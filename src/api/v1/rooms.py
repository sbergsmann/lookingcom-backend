"""Room availability endpoints"""

import asyncio
from fastapi import APIRouter, HTTPException, status
import logfire

from src.schemas.room_availability import (
    RoomAvailabilityRequest,
    RoomAvailabilityResponse,
    RoomRequest,
    ChildRequest,
)
from src.schemas.simplified_search import (
    SimplifiedRoomSearchRequest,
    SimplifiedRoomSearchResponse,
    RoomOptionWithDateRange,
    Language,
)
from src.services.capcorn_client import CapCornClient
from src.services.analytics_service import get_analytics_service
from src.core.config import get_settings

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/search", response_model=SimplifiedRoomSearchResponse)
async def search_rooms(request: SimplifiedRoomSearchRequest):
    """
    Search for available rooms with flexible duration within a timespan.
    
    This endpoint generates all possible date ranges for the specified duration
    within the given timespan and searches them in parallel.
    
    - **language**: "de" for German, "en" for English
    - **timespan**: Date range to search within (from/to)
    - **duration**: Length of stay in days (must be ≤ timespan)
    - **adults**: Number of adults
    - **children**: List of children with their ages
    
    Example: If timespan is 7 days and duration is 4 days, 
    4 parallel queries will be made covering all possible 4-day stays.
    """
    logfire.info(f"Simplified Room Search Request: {request.model_dump()}")
    
    # Log analytics
    analytics = get_analytics_service()
    await analytics.log_room_search(request.model_dump(mode="json"))
    
    try:
        settings = get_settings()
        client = CapCornClient()
        
        # Generate all date ranges
        date_ranges = request.generate_date_ranges()
        
        if not date_ranges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid date ranges could be generated from timespan and duration",
            )
        
        # Convert language to API format (0=German, 1=English)
        language_code = 0 if request.language == Language.GERMAN else 1
        
        # Prepare children data
        children = [ChildRequest(age=child.age) for child in request.children]
        
        # Create parallel requests for all date ranges
        async def search_single_range(arrival_date, departure_date):
            search_request = RoomAvailabilityRequest(
                language=language_code,
                hotel_id=settings.capcorn_hotel_id,
                arrival=arrival_date,
                departure=departure_date,
                rooms=[RoomRequest(adults=request.adults, children=children)],
            )
            return await client.search_room_availability(search_request)
        
        # Execute all searches in parallel
        search_tasks = [
            search_single_range(arrival, departure)
            for arrival, departure in date_ranges
        ]
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Collect all room options from all results
        all_options = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                # Log error but continue with other results
                continue
            
            arrival, departure = date_ranges[idx]
            
            # Extract room options from response
            for member in result.members:
                for room in member.rooms:
                    for option in room.options:
                        all_options.append(
                            RoomOptionWithDateRange(
                                arrival=arrival,
                                departure=departure,
                                catc=option.catc,
                                type=option.type,
                                description=option.description,
                                size=option.size,
                                price=option.price,
                                price_per_person=option.price_per_person,
                                price_per_adult=option.price_per_adult,
                                price_per_night=option.price_per_night,
                                board=option.board,
                                room_type=option.room_type,
                            )
                        )
        
        logfire.info(f"Simplified Room Search found {len(all_options)} options across {len(date_ranges)} queries.")
        logfire.info(f"Room Search Response: {all_options}")
        return SimplifiedRoomSearchResponse(
            total_queries=len(date_ranges),
            total_options=len(all_options),
            duration_days=request.duration,
            options=all_options,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search room availability: {str(e)}",
        )


@router.post("/availability", response_model=RoomAvailabilityResponse)
async def search_room_availability(request: RoomAvailabilityRequest):
    """
    Direct room availability search (original API format).
    
    - **language**: 0 for German, 1 for English
    - **hotel_id**: CapCorn Hotel ID
    - **arrival**: Check-in date
    - **departure**: Check-out date
    - **rooms**: List of rooms with adults and children (max 10 rooms)
    """
    try:
        client = CapCornClient()
        return await client.search_room_availability(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search room availability: {str(e)}",
        )
