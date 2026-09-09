from __future__ import annotations

from agents import function_tool

from .manual import manual_retriever
from .safety import (
    SafetyViolation,
    validate_door_open,
    validate_seat_heat,
    validate_temperature,
    validate_window_percent,
)
from .state import vehicle_state


@function_tool
def get_vehicle_status() -> dict:
    """Get current mock vehicle state including speed, HVAC, seat, window and destination."""
    return vehicle_state.snapshot()


@function_tool
def set_hvac_temperature(temperature_c: float) -> dict:
    """Set cabin HVAC target temperature in Celsius. Allowed range is 16 to 30."""
    validate_temperature(temperature_c)
    return vehicle_state.update(hvac_target_c=round(float(temperature_c), 1))


@function_tool
def set_driver_seat_heating(level: int) -> dict:
    """Set driver seat heating. 0=off, 1=low, 2=medium, 3=high."""
    validate_seat_heat(level)
    return vehicle_state.update(driver_seat_heat_level=level)


@function_tool
def set_driver_window(percent_open: int) -> dict:
    """Set driver window opening percentage, where 0 is closed and 100 is fully open."""
    validate_window_percent(percent_open)
    return vehicle_state.update(driver_window_percent=percent_open)


@function_tool
def set_ambient_light(color: str) -> dict:
    """Set ambient light color using a short color name such as blue, purple or warm white."""
    normalized = color.strip().lower()
    if not normalized:
        raise SafetyViolation("Ambient light color cannot be empty.")
    return vehicle_state.update(ambient_light=normalized)


@function_tool
def start_navigation(destination: str) -> dict:
    """Start mock navigation to a user-provided destination."""
    destination = destination.strip()
    if not destination:
        raise ValueError("Destination cannot be empty.")
    return vehicle_state.update(destination=destination)


@function_tool
def open_left_front_door() -> dict:
    """Open the left-front door. This action is blocked whenever vehicle speed is above 0.5 km/h."""
    status = vehicle_state.snapshot()
    validate_door_open(float(status["speed_kph"]))
    return vehicle_state.update(left_front_door_open=True)


@function_tool
def search_vehicle_manual(query: str) -> dict:
    """Search the local vehicle manual for instructions, warning lights, or feature explanations."""
    results = manual_retriever.search(query, top_k=2)
    return {"query": query, "results": results}


ALL_TOOLS = [
    get_vehicle_status,
    set_hvac_temperature,
    set_driver_seat_heating,
    set_driver_window,
    set_ambient_light,
    start_navigation,
    open_left_front_door,
    search_vehicle_manual,
]
