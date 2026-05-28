import logging
from risk_engine import Thresholds

logger = logging.getLogger(__name__)


class SystemState:
    def __init__(self, thresholds: Thresholds):
        self.armed: bool = False
        self.thresholds: Thresholds = thresholds
        self._was_dark: bool = False

    def auto_arm(self, light_value: int):
        """Arm when light drops below threshold; disarm when it rises above."""
        is_dark = light_value < self.thresholds.light_dark_threshold
        if is_dark and not self._was_dark:
            logger.info("Auto-arming: darkness detected (light=%d)", light_value)
            self.armed = True
        elif not is_dark and self._was_dark:
            logger.info("Auto-disarming: light detected (light=%d)", light_value)
            self.armed = False
        self._was_dark = is_dark

    def manual_arm(self):
        logger.info("Manual arm requested")
        self.armed = True

    def manual_disarm(self):
        logger.info("Manual disarm requested")
        self.armed = False

    def update_thresholds(self, new_thresholds: dict):
        self.thresholds = Thresholds.from_dict({
            **self.thresholds.__dict__,
            **new_thresholds,
        })
        logger.info("Thresholds updated: %s", self.thresholds)
