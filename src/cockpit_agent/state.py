from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import Lock


@dataclass
class VehicleState:
    speed_kph: float = 0.0
    cabin_temperature_c: float = 24.0
    hvac_target_c: float = 24.0
    driver_seat_heat_level: int = 0
    driver_window_percent: int = 0
    ambient_light: str = "blue"
    destination: str | None = None
    left_front_door_open: bool = False


class VehicleStateStore:
    def __init__(self) -> None:
        self._state = VehicleState()
        self._lock = Lock()

    def snapshot(self) -> dict:
        with self._lock:
            return asdict(self._state)

    def update(self, **changes: object) -> dict:
        with self._lock:
            for key, value in changes.items():
                if not hasattr(self._state, key):
                    raise KeyError(f"Unknown vehicle state field: {key}")
                setattr(self._state, key, value)
            return asdict(self._state)

    def reset(self) -> dict:
        with self._lock:
            self._state = VehicleState()
            return asdict(self._state)


vehicle_state = VehicleStateStore()
