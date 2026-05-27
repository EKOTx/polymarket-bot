"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.opportunities import router as opp_router
from backend.app.api.v1.endpoints.trades import router as trades_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(opp_router)
api_router.include_router(trades_router)
