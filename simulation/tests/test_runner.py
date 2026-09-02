from simulation.adapters.idr_adapter import PerfectGroundTruthAdapter
from simulation.runner.engine import SimulationEngine
from simulation.scenario.presets import get_preset_scenarios


def test_deterministic_reproducibility():
    presets = get_preset_scenarios()
    sc1 = presets["flagship_gnss_outage"]
    sc2 = presets["flagship_gnss_outage"]
    sc1.seed = 42
    sc2.seed = 42

    engine1 = SimulationEngine(sc1, idr_adapter=PerfectGroundTruthAdapter(ground_truth_states=[]))
    engine2 = SimulationEngine(sc2, idr_adapter=PerfectGroundTruthAdapter(ground_truth_states=[]))

    res1 = engine1.run()
    res2 = engine2.run()

    # Verify sensor streams are identical
    rec1 = res1["sensor_records"]
    rec2 = res2["sensor_records"]

    assert len(rec1) == len(rec2)
    assert rec1[0]["ACC_MAG"] == rec2[0]["ACC_MAG"]
    assert rec1[10]["ax"] == rec2[10]["ax"]
