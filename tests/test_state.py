from cockpit_agent.state import VehicleStateStore


def test_state_update_and_reset() -> None:
    store = VehicleStateStore()
    store.update(hvac_target_c=22.0)
    assert store.snapshot()["hvac_target_c"] == 22.0
    store.reset()
    assert store.snapshot()["hvac_target_c"] == 24.0
