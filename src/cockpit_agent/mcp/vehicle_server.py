from __future__ import annotations

from mcp.server import MCPServer

from cockpit_agent.safety import (
    SafetyViolation,
    validate_door_open,
    validate_seat_heat,
    validate_temperature,
    validate_window_percent,
)
from cockpit_agent.state import vehicle_state


mcp = MCPServer(
    "AI Cockpit Vehicle Server"
)


@mcp.resource(
    "vehicle://state",
    mime_type="application/json",
)
def get_vehicle_state() -> dict:
    """Return the current mock vehicle state."""

    return vehicle_state.snapshot()


@mcp.tool()
def get_vehicle_status() -> dict:
    """Get the current mock vehicle status."""

    return vehicle_state.snapshot()


@mcp.tool()
def set_hvac_temperature(
    temperature_c: float,
) -> dict:
    """Set HVAC target temperature in Celsius.

    Allowed range: 16°C to 30°C.
    """

    validate_temperature(
        temperature_c
    )

    return vehicle_state.update(
        hvac_target_c=round(
            float(temperature_c),
            1,
        )
    )


@mcp.tool()
def set_driver_seat_heating(
    level: int,
) -> dict:
    """Set driver seat heating.

    0=off, 1=low, 2=medium, 3=high.
    """

    validate_seat_heat(level)

    return vehicle_state.update(
        driver_seat_heat_level=level
    )


@mcp.tool()
def set_driver_window(
    percent_open: int,
) -> dict:
    """Set driver window opening percentage.

    0 means fully closed.
    100 means fully open.
    """

    validate_window_percent(
        percent_open
    )

    return vehicle_state.update(
        driver_window_percent=percent_open
    )


@mcp.tool()
def set_ambient_light(
    color: str,
) -> dict:
    """Set ambient light color."""

    normalized = (
        color
        .strip()
        .lower()
    )

    if not normalized:
        raise SafetyViolation(
            "Ambient light color "
            "cannot be empty."
        )

    return vehicle_state.update(
        ambient_light=normalized
    )


@mcp.tool()
def start_navigation(
    destination: str,
) -> dict:
    """Start mock navigation."""

    destination = (
        destination.strip()
    )

    if not destination:
        raise ValueError(
            "Destination cannot be empty."
        )

    return vehicle_state.update(
        destination=destination
    )


@mcp.tool()
def open_left_front_door() -> dict:
    """Open the left-front door.

    The action is rejected when
    vehicle speed is above 0.5 km/h.
    """

    state = (
        vehicle_state.snapshot()
    )

    validate_door_open(
        float(
            state["speed_kph"]
        )
    )

    return vehicle_state.update(
        left_front_door_open=True
    )


if __name__ == "__main__":
    mcp.run()