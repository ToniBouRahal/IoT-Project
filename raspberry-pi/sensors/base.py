from abc import ABC, abstractmethod


class BaseSensor(ABC):
    @abstractmethod
    def read(self) -> dict:
        """Read sensor value and return a dict of named readings."""
        ...
