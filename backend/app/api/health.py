from fastapi import APIRouter
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.mqtt.subscriber import is_connected as mqtt_connected

router = APIRouter()


@router.get("/health")
async def health():
    db_ok = False
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "db": db_ok,
        "mqtt": mqtt_connected(),
    }
