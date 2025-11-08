"""API v1 router aggregation"""

from fastapi import APIRouter

from src.api.v1 import rooms, reservations

api_router = APIRouter(prefix="/v1")

api_router.include_router(rooms.router)
api_router.include_router(reservations.router)
