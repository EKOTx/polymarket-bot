"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints.alerts import router as alerts_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.billing import router as billing_router
from backend.app.api.v1.endpoints.markets import router as markets_router
from backend.app.api.v1.endpoints.opportunities import router as opp_router
from backend.app.api.v1.endpoints.public import router as public_router
from backend.app.api.v1.endpoints.trades import router as trades_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(opp_router)
api_router.include_router(trades_router)
api_router.include_router(alerts_router)
api_router.include_router(markets_router)
api_router.include_router(public_router)
api_router.include_router(billing_router)
