import logging
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from simulation.runner.engine import SimulationEngine
from simulation.scenario.presets import get_preset_scenarios
from simulation.scenario.schema import SimulationScenario
from .models import SimulationRun

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_simulation_job_task(self, simulation_run_id: str):
    """
    Asynchronous Celery task that executes a simulation run outside the HTTP request loop.
    """
    try:
        run_obj = SimulationRun.objects.get(pk=simulation_run_id)
    except SimulationRun.DoesNotExist:
        logger.error("SimulationRun with ID %s not found.", simulation_run_id)
        return

    run_obj.status = SimulationRun.Status.RUNNING
    run_obj.started_at = timezone.now()
    run_obj.save(update_fields=["status", "started_at"])

    try:
        # Load preset scenario or reconstruct from config
        presets = get_preset_scenarios()
        scenario_id = run_obj.scenario_id

        if scenario_id in presets:
            scenario = presets[scenario_id]
        else:
            scenario = presets.get("flagship_gnss_outage")

        # Apply custom seed/duration overrides if specified
        scenario.seed = run_obj.seed
        if run_obj.duration_seconds > 0:
            scenario.duration_seconds = run_obj.duration_seconds

        # Filter and clamp outages to scenario duration
        valid_outages = []
        for o in scenario.gnss.outages:
            if o.start_seconds < scenario.duration_seconds:
                o.end_seconds = min(o.end_seconds, scenario.duration_seconds)
                if o.start_seconds < o.end_seconds:
                    valid_outages.append(o)
        scenario.gnss.outages = valid_outages

        # Output artifact directory under MEDIA_ROOT
        media_root = getattr(settings, "MEDIA_ROOT", Path(__file__).resolve().parent.parent.parent / "media")
        output_dir = Path(media_root) / "simulations" / str(run_obj.id)
        output_dir.mkdir(parents=True, exist_ok=True)

        engine = SimulationEngine(scenario=scenario)
        exec_res = engine.run(output_dir=output_dir)

        res_data = exec_res.get("result", {})

        run_obj.status = SimulationRun.Status.COMPLETED
        run_obj.completed_at = timezone.now()
        run_obj.metrics = res_data.get("metrics", {})
        run_obj.gnss_outage_evaluations = res_data.get("gnss_outage_evaluations", [])
        run_obj.artifact_paths = {
            "ground_truth_csv": f"/media/simulations/{run_obj.id}/ground_truth.csv",
            "sensor_stream_csv": f"/media/simulations/{run_obj.id}/sensor_stream.csv",
            "evaluation_report_json": f"/media/simulations/{run_obj.id}/evaluation_report.json",
        }
        run_obj.save()

        logger.info("Celery task completed simulation %s successfully.", simulation_run_id)

    except Exception as exc:
        logger.exception("Simulation task failed for ID %s: %s", simulation_run_id, exc)
        run_obj.status = SimulationRun.Status.FAILED
        run_obj.completed_at = timezone.now()
        run_obj.error_message = str(exc)
        run_obj.save(update_fields=["status", "completed_at", "error_message"])
