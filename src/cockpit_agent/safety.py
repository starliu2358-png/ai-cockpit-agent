from __future__ import annotations


class SafetyViolation(ValueError):
    """Raised when a requested cockpit action violates a hard safety rule."""


def validate_temperature(value_c: float) -> None:
    if not 16.0 <= value_c <= 30.0:
        raise SafetyViolation("HVAC temperature must be between 16°C and 30°C.")


def validate_seat_heat(level: int) -> None:
    if level not in {0, 1, 2, 3}:
        raise SafetyViolation("Seat heating level must be 0, 1, 2, or 3.")


def validate_window_percent(percent: int) -> None:
    if not 0 <= percent <= 100:
        raise SafetyViolation("Window opening percentage must be between 0 and 100.")


def validate_door_open(speed_kph: float) -> None:
    if speed_kph > 0.5:
        raise SafetyViolation("The door cannot be opened while the vehicle is moving.")
