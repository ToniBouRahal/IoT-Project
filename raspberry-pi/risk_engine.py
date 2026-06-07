from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Thresholds:
    light_dark_threshold: int = 50
    flame_fire_score: float = 0.7
    temp_high_c: float = 40.0
    temp_extreme_c: float = 60.0
    humidity_low_pct: float = 30.0
    fire_confirm_score: float = 0.8
    fire_alarm_score: float = 0.5

    @classmethod
    def from_dict(cls, d: dict) -> "Thresholds":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class RiskEngine:
    def classify(
        self,
        light: int,
        flame_detected: bool,
        temperature_c: float,
        humidity_percent: float,
        motion_detected: bool,
        armed: bool,
        thresholds: Thresholds,
    ) -> tuple[str, float]:
        """Return (threat_label, risk_score) for the current sensor sample.

        Fire is evaluated first and takes priority over intruder detection.
        """
        fire_score = self._fire_score(
            flame_detected, temperature_c, humidity_percent, thresholds
        )

        if fire_score >= thresholds.fire_confirm_score:
            return ("Fire", round(fire_score, 3))

        if fire_score >= thresholds.fire_alarm_score:
            return ("False Alarm", round(fire_score, 3))

        if motion_detected and armed:
            return ("Intruder", 0.8)

        return ("Safe", round(fire_score, 3))

    def _fire_score(
        self,
        flame_detected: bool,
        temperature_c: float,
        humidity_percent: float,
        t: Thresholds,
    ) -> float:
        score = 0.0

        if flame_detected:
            score += t.flame_fire_score

        if temperature_c > t.temp_extreme_c:
            score += 0.5
        elif temperature_c > t.temp_high_c:
            score += 0.3

        if humidity_percent < t.humidity_low_pct:
            score += 0.2

        return min(score, 1.0)
