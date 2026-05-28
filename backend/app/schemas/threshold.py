from pydantic import BaseModel, Field


class ThresholdOut(BaseModel):
    device_id: str
    light_dark_threshold: int
    flame_fire_score: float
    temp_high_c: float
    temp_extreme_c: float
    humidity_low_pct: float
    fire_confirm_score: float
    fire_alarm_score: float

    model_config = {"from_attributes": True}


class ThresholdUpdate(BaseModel):
    light_dark_threshold: int | None = Field(None, ge=0, le=1023)
    flame_fire_score: float | None = Field(None, ge=0.0, le=1.0)
    temp_high_c: float | None = None
    temp_extreme_c: float | None = None
    humidity_low_pct: float | None = Field(None, ge=0.0, le=100.0)
    fire_confirm_score: float | None = Field(None, ge=0.0, le=1.0)
    fire_alarm_score: float | None = Field(None, ge=0.0, le=1.0)
