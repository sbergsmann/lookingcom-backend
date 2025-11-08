"""Analytics service for tracking searches and bookings"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import asyncio
from pydantic import BaseModel


class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    timestamp: datetime
    event_type: str  # "room_search" or "reservation"
    data: dict[str, Any]


class AnalyticsService:
    """Service for logging and retrieving analytics data"""
    
    def __init__(self, log_dir: str = "analytics_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.search_log_file = self.log_dir / "room_searches.jsonl"
        self.reservation_log_file = self.log_dir / "reservations.jsonl"
        self._lock = asyncio.Lock()
    
    async def log_room_search(self, search_data: dict[str, Any]) -> None:
        """Log a room search event"""
        event = AnalyticsEvent(
            timestamp=datetime.utcnow(),
            event_type="room_search",
            data=search_data
        )
        await self._write_log(self.search_log_file, event)
    
    async def log_reservation(self, reservation_data: dict[str, Any]) -> None:
        """Log a reservation event"""
        event = AnalyticsEvent(
            timestamp=datetime.utcnow(),
            event_type="reservation",
            data=reservation_data
        )
        await self._write_log(self.reservation_log_file, event)
    
    async def _write_log(self, file_path: Path, event: AnalyticsEvent) -> None:
        """Write event to log file (JSONL format)"""
        async with self._lock:
            with open(file_path, "a", encoding="utf-8") as f:
                json_str = json.dumps({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "data": event.data
                })
                f.write(json_str + "\n")
    
    async def get_room_searches(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get room searches from the last N hours"""
        return await self._read_logs(self.search_log_file, hours)
    
    async def get_reservations(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get reservations from the last N hours"""
        return await self._read_logs(self.reservation_log_file, hours)
    
    async def _read_logs(self, file_path: Path, hours: int) -> list[dict[str, Any]]:
        """Read logs from file and filter by timespan"""
        if not file_path.exists():
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        events = []
        
        async with self._lock:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        if event_time >= cutoff_time:
                            events.append(event)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed lines
                        continue
        
        return events
    
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
        
        # Get popular destinations (room types)
        room_types = {}
        for search in searches:
            duration = search.get("data", {}).get("duration", 0)
            room_types[duration] = room_types.get(duration, 0) + 1
        
        return {
            "timespan_hours": hours,
            "total_searches": total_searches,
            "total_reservations": total_reservations,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "popular_durations": dict(sorted(room_types.items(), key=lambda x: x[1], reverse=True)[:5]),
            "searches": searches,
            "reservations": reservations
        }


# Singleton instance
_analytics_service: AnalyticsService | None = None


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service singleton"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
