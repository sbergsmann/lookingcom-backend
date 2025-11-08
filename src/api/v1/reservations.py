"""Reservation/booking endpoints"""

from fastapi import APIRouter, HTTPException, status
import logfire

from src.schemas.reservation import ReservationRequest, ReservationResponse
from src.services.capcorn_client import CapCornClient
from src.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(request: ReservationRequest):
    """
    Create a new hotel reservation.
    
    Hotel ID is automatically set to 9100 (fixed).
    
    - **room_type_code**: Room category code from availability search
    - **meal_plan**: Included meals (default: Breakfast). Options: 1=Breakfast, 2=Half board, 3=Full board, 4=No meals, 5=All inclusive
    - **guest_counts**: Adults and children counts
    - **arrival/departure**: Stay dates
    - **total_amount**: Total price in EUR
    - **guest**: Guest information
    - **services**: Optional additional services
    - **reservation_id**: Unique booking ID from your system
    - **source**: Source/channel name (default: LookingCom)
    """
    try:
        # Log analytics
        analytics = get_analytics_service()
        await analytics.log_reservation(request.model_dump(mode="json"))
        
        client = CapCornClient()
        logfire.info(f"Creating reservation with request: {request.model_dump()}")
        response = await client.create_reservation(request)
        
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message,
            )
        
        logfire.info(f"Reservation created successfully: {response}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reservation: {str(e)}",
        )
