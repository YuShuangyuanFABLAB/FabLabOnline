"""V1 API 路由聚合"""
from fastapi import APIRouter

from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.campuses import router as campuses_router
from api.v1.roles import router as roles_router
from api.v1.events import router as events_router
from api.v1.analytics import router as analytics_router
from api.v1.apps import router as apps_router
from api.v1.config import router as config_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(campuses_router)
router.include_router(roles_router)
router.include_router(events_router)
router.include_router(analytics_router)
router.include_router(apps_router)
router.include_router(config_router)
