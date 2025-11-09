"""Analytics service for tracking searches and bookings"""

from datetime import datetime, timedelta
from typing import Any
import asyncio
from pydantic import BaseModel
from collections import deque


class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    timestamp: datetime
    event_type: str  # "room_search" or "reservation"
    data: dict[str, Any]
    results_count: int | None = None  # Number of room options found (for searches)


class AnalyticsService:
    """Service for logging and retrieving analytics data (in-memory)"""
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize analytics service with in-memory storage.
        
        Args:
            max_events: Maximum number of events to keep in memory per type
        """
        self._room_searches: deque[AnalyticsEvent] = deque(maxlen=max_events)
        self._reservations: deque[AnalyticsEvent] = deque(maxlen=max_events)
        self._lock = asyncio.Lock()
    
    async def log_room_search(self, search_data: dict[str, Any], results_count: int = 0) -> None:
        """
        Log a room search event
        
        Args:
            search_data: The search request data
            results_count: Number of room options found in the search results
        """
        event = AnalyticsEvent(
            timestamp=datetime.utcnow(),
            event_type="room_search",
            data=search_data,
            results_count=results_count
        )
        async with self._lock:
            self._room_searches.append(event)
    
    async def log_reservation(self, reservation_data: dict[str, Any]) -> None:
        """Log a reservation event"""
        event = AnalyticsEvent(
            timestamp=datetime.utcnow(),
            event_type="reservation",
            data=reservation_data
        )
        async with self._lock:
            self._reservations.append(event)
    
    async def get_room_searches(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get room searches from the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with self._lock:
            filtered_events = [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "data": event.data,
                    "results_count": event.results_count
                }
                for event in self._room_searches
                if event.timestamp >= cutoff_time
            ]
        
        return filtered_events
    
    async def get_reservations(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get reservations from the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with self._lock:
            filtered_events = [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "data": event.data
                }
                for event in self._reservations
                if event.timestamp >= cutoff_time
            ]
        
        return filtered_events
    
    async def get_analytics_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get analytics summary for the specified timespan"""
        searches = await self.get_room_searches(hours)
        reservations = await self.get_reservations(hours)
        
        # Calculate summary statistics
        total_searches = len(searches)
        total_reservations = len(reservations)
        conversion_rate = (total_reservations / total_searches * 100) if total_searches > 0 else 0
        
        # Calculate total revenue
        total_revenue = sum(
            res.get("data", {}).get("total_amount", 0)
            for res in reservations
        )
        
        # Get popular durations from searches
        room_durations = {}
        for search in searches:
            duration = search.get("data", {}).get("duration", 0)
            if duration > 0:
                room_durations[duration] = room_durations.get(duration, 0) + 1
        
        # Get average booking value
        avg_booking_value = total_revenue / total_reservations if total_reservations > 0 else 0
        
        # Calculate total rooms found across all searches
        total_rooms_found = sum(
            search.get("results_count", 0) or 0
            for search in searches
        )
        avg_results_per_search = total_rooms_found / total_searches if total_searches > 0 else 0
        
        return {
            "timespan_hours": hours,
            "total_searches": total_searches,
            "total_reservations": total_reservations,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "average_booking_value": round(avg_booking_value, 2),
            "total_rooms_found": total_rooms_found,
            "average_results_per_search": round(avg_results_per_search, 2),
            "popular_durations": dict(sorted(room_durations.items(), key=lambda x: x[1], reverse=True)[:5]),
            "searches": searches,
            "reservations": reservations
        }
    
    async def get_stats(self) -> dict[str, Any]:
        """Get overall statistics about stored events"""
        async with self._lock:
            return {
                "total_searches_in_memory": len(self._room_searches),
                "total_reservations_in_memory": len(self._reservations),
                "oldest_search": self._room_searches[0].timestamp.isoformat() if self._room_searches else None,
                "newest_search": self._room_searches[-1].timestamp.isoformat() if self._room_searches else None,
                "oldest_reservation": self._reservations[0].timestamp.isoformat() if self._reservations else None,
                "newest_reservation": self._reservations[-1].timestamp.isoformat() if self._reservations else None,
            }


# Singleton instance
_analytics_service: AnalyticsService | None = None


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service singleton"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
