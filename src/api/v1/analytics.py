"""Analytics endpoints"""

from fastapi import APIRouter, Query
from typing import Annotated

from src.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(
    hours: Annotated[int, Query(ge=1, le=24, description="Number of hours to look back (1-24)")] = 24
):
    """
    Get analytics summary for room searches and reservations.
    
    Returns aggregated statistics and detailed logs for the specified timespan.
    Data is stored in-memory, so only events since the last server restart are available.
    
    - **hours**: Number of hours to look back (1-24, default: 24)
    
    Response includes:
    - Total searches and reservations
    - Conversion rate
    - Total revenue
    - Average booking value
    - Popular durations
    - Detailed search and reservation logs
    """
    analytics = get_analytics_service()
    return await analytics.get_analytics_summary(hours)


# @router.get("/searches")
# async def get_room_searches(
#     hours: Annotated[int, Query(ge=1, le=24, description="Number of hours to look back (1-24)")] = 24
# ):
#     """
#     Get room search logs for the specified timespan.
    
#     Data is stored in-memory (max 10,000 events per type).
    
#     - **hours**: Number of hours to look back (1-24, default: 24)
#     """
#     analytics = get_analytics_service()
#     searches = await analytics.get_room_searches(hours)
#     return {
#         "timespan_hours": hours,
#         "total_searches": len(searches),
#         "searches": searches
#     }


# @router.get("/reservations")
# async def get_reservations(
#     hours: Annotated[int, Query(ge=1, le=24, description="Number of hours to look back (1-24)")] = 24
# ):
#     """
#     Get reservation logs for the specified timespan.
    
#     Data is stored in-memory (max 10,000 events per type).
    
#     - **hours**: Number of hours to look back (1-24, default: 24)
#     """
#     analytics = get_analytics_service()
#     reservations = await analytics.get_reservations(hours)
    
#     # Calculate total revenue
#     total_revenue = sum(
#         res.get("data", {}).get("total_amount", 0)
#         for res in reservations
#     )
    
#     return {
#         "timespan_hours": hours,
#         "total_reservations": len(reservations),
#         "total_revenue": round(total_revenue, 2),
#         "reservations": reservations
#     }


# @router.get("/stats")
# async def get_stats():
#     """
#     Get overall statistics about the in-memory analytics storage.
    
#     Returns information about total events stored and time ranges.
#     """
#     analytics = get_analytics_service()
#     return await analytics.get_stats()
