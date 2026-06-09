from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Thresholds:
    light_dark_threshold: int = 50
    flame_fire_score: float = 0.7
    temp_high_c: float = 40.0
    temp_extreme_c: float = 60.0
    humidity_low_pct: float = 30.0
    fire_confirm_score: float = 0.8   # kept for schema compatibility, not used in logic
    fire_alarm_score: float = 0.5     # kept for schema compatibility, not used in logic

    @classmethod
    def from_dict(cls, d: dict) -> "Thresholds":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class RiskEngine:
    def __init__(self):
        self._prev_temp: float | None = None

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
        """Classify the current environment into a threat label with a risk score.

        Priority order: fire-family checks first, then Intruder, then Safe.

        Labels:
          Fire          — flame + elevated temp or low humidity, and temp not falling
          Possible Fire — flame detected but no environmental confirmation yet
          False Alarm   — elevated temp/humidity without flame, OR flame + falling temp
          Intruder      — motion while armed (only when no fire-family condition is active)
          Safe          — no threat detected
        """
        temp_elevated = temperature_c > thresholds.temp_high_c
        temp_extreme  = temperature_c > thresholds.temp_extreme_c
        humidity_low  = humidity_percent < thresholds.humidity_low_pct
        env_confirmed = temp_elevated or humidity_low

        # True only when we have a previous reading and temperature has dropped
        temp_decreasing = (
            self._prev_temp is not None and temperature_c < self._prev_temp
        )
        self._prev_temp = temperature_c

        if flame_detected:
            if temp_decreasing:
                # Flame still present but conditions cooling — likely a passing/brief source
                return ("False Alarm", round(thresholds.flame_fire_score * 0.6, 3))

            if env_confirmed:
                # Flame + heat or dryness confirmed → real fire
                score = thresholds.flame_fire_score
                score += 0.2 if temp_extreme else 0.1 if temp_elevated else 0.0
                score += 0.1 if humidity_low else 0.0
                return ("Fire", round(min(score, 1.0), 3))

            # Flame alone with no environmental confirmation yet
            return ("Possible Fire", round(thresholds.flame_fire_score, 3))

        if env_confirmed:
            # Elevated temp or low humidity with no flame — environmental warning
            score = 0.3 if temp_extreme else 0.2 if temp_elevated else 0.0
            score += 0.15 if humidity_low else 0.0
            return ("False Alarm", round(score, 3))

        if motion_detected and armed:
            return ("Intruder", 0.8)

        return ("Safe", 0.0)
