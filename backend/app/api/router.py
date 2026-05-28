from fastapi import APIRouter

from app.api import auth, commands, devices, health, thresholds

router = APIRouter(prefix="/api")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(devices.router)
router.include_router(commands.router)
router.include_router(thresholds.router)
