from simulation.runner.engine import SimulationEngine
from simulation.scenario.presets import get_preset_scenarios


def test_gnss_outage_suppression():
    presets = get_preset_scenarios()
    sc = presets["gnss_outage"]  # Outage from t=60 to t=120
    engine = SimulationEngine(sc)
    res = engine.run()

    gnss_records = [r for r in res["sensor_records"] if r.get("sensor") == "GNSS"]

    outage_records = [r for r in gnss_records if 60.0 <= r["timestamp"] <= 120.0]

    # Verify all GNSS records during outage are marked UNAVAILABLE with lat=None
    for r in outage_records:
        assert r["status"] == "UNAVAILABLE"
        assert r["latitude"] is None
        assert r["longitude"] is None
