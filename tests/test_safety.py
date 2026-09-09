import pytest

from cockpit_agent.safety import (
    SafetyViolation,
    validate_door_open,
    validate_seat_heat,
    validate_temperature,
    validate_window_percent,
)


def test_temperature_range() -> None:
    validate_temperature(23)
    with pytest.raises(SafetyViolation):
        validate_temperature(35)


def test_seat_heat_range() -> None:
    validate_seat_heat(2)
    with pytest.raises(SafetyViolation):
        validate_seat_heat(4)


def test_window_range() -> None:
    validate_window_percent(50)
    with pytest.raises(SafetyViolation):
        validate_window_percent(120)


def test_door_open_blocked_while_moving() -> None:
    validate_door_open(0)
    with pytest.raises(SafetyViolation):
        validate_door_open(20)
