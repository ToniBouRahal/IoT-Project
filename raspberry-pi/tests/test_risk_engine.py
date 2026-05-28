import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from risk_engine import RiskEngine, Thresholds

engine = RiskEngine()
t = Thresholds()  # default thresholds


def classify(**kwargs):
    defaults = dict(
        light=200, flame_detected=False, temperature_c=25.0,
        humidity_percent=55.0, motion_detected=False, armed=False,
    )
    defaults.update(kwargs)
    return engine.classify(**defaults, thresholds=t)


class TestFireClassification:
    def test_flame_alone_returns_fire(self):
        threat, score = classify(flame_detected=True)
        assert threat == "Fire"
        assert score >= t.fire_confirm_score

    def test_flame_plus_high_temp_plus_low_humidity_is_fire(self):
        threat, score = classify(
            flame_detected=True, temperature_c=45.0, humidity_percent=20.0
        )
        assert threat == "Fire"
        assert score == 1.0  # capped

    def test_extreme_temp_only_is_false_alarm(self):
        # temp_extreme alone = 0.5 which is >= fire_alarm_score but < fire_confirm_score
        threat, score = classify(temperature_c=65.0)
        assert threat == "False Alarm"
        assert t.fire_alarm_score <= score < t.fire_confirm_score

    def test_high_temp_and_low_humidity_is_false_alarm(self):
        # 0.3 + 0.2 = 0.5 = fire_alarm_score
        threat, score = classify(temperature_c=45.0, humidity_percent=20.0)
        assert threat == "False Alarm"

    def test_safe_conditions(self):
        threat, score = classify()
        assert threat == "Safe"
        assert score < t.fire_alarm_score


class TestIntruderClassification:
    def test_motion_while_armed_is_intruder(self):
        threat, score = classify(motion_detected=True, armed=True)
        assert threat == "Intruder"
        assert score == 0.8

    def test_motion_while_disarmed_is_safe(self):
        threat, score = classify(motion_detected=True, armed=False)
        assert threat == "Safe"

    def test_no_motion_while_armed_is_safe(self):
        threat, score = classify(armed=True)
        assert threat == "Safe"


class TestFirePriorityOverIntruder:
    def test_flame_beats_motion_and_armed(self):
        # Fire should be returned even when armed + motion
        threat, score = classify(flame_detected=True, motion_detected=True, armed=True)
        assert threat == "Fire"


class TestScoreCap:
    def test_score_never_exceeds_1(self):
        threat, score = classify(
            flame_detected=True, temperature_c=70.0, humidity_percent=10.0
        )
        assert score <= 1.0
