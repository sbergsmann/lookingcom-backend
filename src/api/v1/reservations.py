"""Reservation/booking endpoints"""

from fastapi import APIRouter, HTTPException, status

from src.schemas.reservation import ReservationRequest, ReservationResponse
from src.services.capcorn_client import CapCornClient

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(request: ReservationRequest):
    """
    Create a new hotel reservation.
    
    - **hotel_id**: CapCorn Hotel ID
    - **room_type_code**: Room category code from availability search
    - **meal_plan**: Included meals (1-5)
    - **guest_counts**: Adults and children counts
    - **arrival/departure**: Stay dates
    - **total_amount**: Total price in EUR
    - **guest**: Guest information
    - **services**: Optional additional services
    - **reservation_id**: Unique booking ID from your system
    """
    try:
        client = CapCornClient()
        response = await client.create_reservation(request)
        
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message,
            )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reservation: {str(e)}",
        )
