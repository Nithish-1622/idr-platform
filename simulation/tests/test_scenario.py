import pytest
from simulation.scenario.presets import get_preset_scenarios
from simulation.scenario.schema import SimulationScenario
from simulation.scenario.validator import ScenarioValidationError, validate_scenario


def test_scenario_validation_success():
    presets = get_preset_scenarios()
    scenario = presets["flagship_gnss_outage"]
    valid, msg = validate_scenario(scenario)
    assert valid is True
    assert msg == "OK"


def test_scenario_validation_invalid_duration():
    scenario = SimulationScenario(scenario_id="invalid", name="Invalid", duration_seconds=-10.0)
    with pytest.raises(ScenarioValidationError, match="duration_seconds must be positive"):
        validate_scenario(scenario)


def test_scenario_validation_invalid_outage():
    presets = get_preset_scenarios()
    scenario = presets["gnss_outage"]
    scenario.gnss.outages[0].end_seconds = 500.0  # Exceeds duration
    with pytest.raises(ScenarioValidationError, match="exceeds scenario duration"):
        validate_scenario(scenario)
