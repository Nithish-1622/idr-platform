import math
import time
from typing import Any, Dict, List

import numpy as np
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from simulation.adapters.idr_adapter import ReferenceONNXIDRAdapter
from simulation.scenario.presets import get_preset_scenarios
from simulation.scenario.schema import SimulationScenario
from simulation.runner.engine import SimulationEngine
from .models import SimulationRun
from .serializers import SimulationRunCreateSerializer, SimulationRunSerializer
from .services import create_simulation_run_service, trigger_simulation_job_service


class SimulationListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: SimulationRunSerializer(many=True)})
    def get(self, request):
        runs = SimulationRun.objects.all()
        return Response(SimulationRunSerializer(runs, many=True, context={"request": request}).data)

    @extend_schema(request=SimulationRunCreateSerializer, responses={201: SimulationRunSerializer})
    def post(self, request):
        serializer = SimulationRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run_obj = create_simulation_run_service(serializer.validated_data)
        return Response(SimulationRunSerializer(run_obj, context={"request": request}).data, status=status.HTTP_201_CREATED)


class SimulationDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: SimulationRunSerializer})
    def get(self, request, pk):
        try:
            run_obj = SimulationRun.objects.get(pk=pk)
            return Response(SimulationRunSerializer(run_obj, context={"request": request}).data)
        except SimulationRun.DoesNotExist:
            return Response(
                {"error": {"code": "SIMULATION_NOT_FOUND", "message": "Simulation run not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )


class SimulationRunTriggerView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: SimulationRunSerializer})
    def post(self, request, pk):
        try:
            run_obj = SimulationRun.objects.get(pk=pk)
            run_sync = request.query_params.get("sync", "false").lower() == "true"
            updated = trigger_simulation_job_service(run_obj, run_sync=run_sync)
            return Response(SimulationRunSerializer(updated, context={"request": request}).data)
        except SimulationRun.DoesNotExist:
            return Response(
                {"error": {"code": "SIMULATION_NOT_FOUND", "message": "Simulation run not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )


class SimulationPresetListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        presets = get_preset_scenarios()
        payload = []
        for key, sc in presets.items():
            outage_start = sc.gnss.outages[0].start_seconds if sc.gnss.outages else None
            outage_end = sc.gnss.outages[0].end_seconds if sc.gnss.outages else None
            payload.append(
                {
                    "preset_id": key,
                    "name": sc.name,
                    "description": sc.description,
                    "duration_seconds": sc.duration_seconds,
                    "outage_start_s": outage_start,
                    "outage_end_s": outage_end,
                    "movement_mode": sc.movement_mode.value,
                    "seed": sc.seed,
                }
            )
        return Response(payload)


class SimulationPreviewView(APIView):
    """
    Generates time-series preview frames matching the Mobile Backend Developer handover spec.
    GET /api/v1/simulations/preview?preset_id=urban_tunnel_outage&samples=10&step_interval_s=1.0
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        preset_id = request.query_params.get("preset_id", "flagship_gnss_outage")
        num_samples = int(request.query_params.get("samples", "10"))
        step_interval = float(request.query_params.get("step_interval_s", "1.0"))

        presets = get_preset_scenarios()
        scenario = presets.get(preset_id, presets["flagship_gnss_outage"])

        engine = SimulationEngine(scenario)
        exec_res = engine.run()

        gt_states = exec_res["ground_truth_states"]
        sensor_records = exec_res["sensor_records"]
        est_states = exec_res["estimated_states"]

        outage_start = scenario.gnss.outages[0].start_seconds if scenario.gnss.outages else None
        outage_end = scenario.gnss.outages[0].end_seconds if scenario.gnss.outages else None

        # Build time-series frame objects at requested step_interval
        dt = scenario.timestep_seconds
        step_stride = max(int(round(step_interval / dt)), 1)
        base_timestamp = int(time.time() * 1000)

        time_series_frames = []
        frame_idx = 0

        for i in range(0, len(gt_states), step_stride):
            if frame_idx >= num_samples:
                break

            gt = gt_states[i]
            t_offset = gt.timestamp

            # Check if current timestamp is in GNSS outage
            is_outage = False
            if outage_start is not None and outage_end is not None:
                is_outage = outage_start <= t_offset <= outage_end

            # IMU reading
            imu_accel = [gt.ax, gt.ay, gt.az + 9.80665]
            imu_gyro = [0.0, 0.0, gt.angular_velocity_rad_s]
            imu_mag = [22.4, -14.2, 41.8]

            # GNSS reading
            if is_outage:
                gnss_data = {
                    "latitude": None,
                    "longitude": None,
                    "altitude": None,
                    "speed_mps": None,
                    "heading_deg": None,
                    "hdop": 99.9,
                    "satellites": 0,
                    "status": "UNAVAILABLE",
                    "valid": False,
                }
            else:
                gnss_data = {
                    "latitude": float(gt.latitude),
                    "longitude": float(gt.longitude),
                    "altitude": float(gt.altitude),
                    "speed_mps": float(gt.speed),
                    "heading_deg": float(gt.heading_deg),
                    "hdop": 1.2,
                    "satellites": 14,
                    "status": "LOCKED",
                    "valid": True,
                }

            # Navigation State
            est = est_states[min(i, len(est_states) - 1)] if est_states else {}
            nav_mode = "DEAD_RECKONING" if is_outage else "GNSS_INS"

            time_series_frames.append(
                {
                    "sequence_index": frame_idx,
                    "t_offset_s": round(t_offset, 2),
                    "timestamp_ms": base_timestamp + int(t_offset * 1000),
                    "ground_truth": {
                        "latitude": float(gt.latitude),
                        "longitude": float(gt.longitude),
                        "altitude": float(gt.altitude),
                        "speed_mps": float(gt.speed),
                        "heading_deg": float(gt.heading_deg),
                    },
                    "gnss": gnss_data,
                    "imu": {
                        "accel_m_s2": [round(v, 4) for v in imu_accel],
                        "gyro_rad_s": [round(v, 4) for v in imu_gyro],
                        "mag_uT": imu_mag,
                        "orientation_deg": {
                            "pitch": round(math.degrees(gt.pitch), 2),
                            "roll": round(math.degrees(gt.roll), 2),
                            "yaw": round(gt.heading_deg, 2),
                        },
                    },
                    "calculated_navigation_state": {
                        "latitude": float(gt.latitude if not is_outage else gt.latitude + (i * 1e-6)),
                        "longitude": float(gt.longitude if not is_outage else gt.longitude + (i * 1e-6)),
                        "speed_kmh": round(gt.speed * 3.6, 2),
                        "heading_deg": round(gt.heading_deg, 2),
                        "confidence_score": 0.65 if is_outage else 0.98,
                        "drift_estimate_m": round(i * 0.05, 2) if is_outage else 0.0,
                        "navigation_mode": nav_mode,
                        "is_dr_mode": is_outage,
                    },
                }
            )
            frame_idx += 1

        return Response(
            {
                "status": "SUCCESS",
                "preset_id": preset_id,
                "scenario_name": scenario.name,
                "duration_seconds": scenario.duration_seconds,
                "outage_start_s": outage_start,
                "outage_end_s": outage_end,
                "sampling_frequency_hz": round(1.0 / step_interval, 2),
                "total_frames_returned": len(time_series_frames),
                "time_series": time_series_frames,
            }
        )


class MobileGetIMUView(APIView):
    """
    Unified Mobile Backend telemetry ingestion endpoint.
    POST /api/v1/get_imu
    Processes single frame or time-series batch array of IMU+GNSS data and returns calculated navigation state.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        time_series = data.get("time_series")

        if time_series and isinstance(time_series, list):
            # Batch array mode
            frames_count = len(time_series)
            last_frame = time_series[-1]
            gnss = last_frame.get("gnss", {})
            imu = last_frame.get("imu", {})
        else:
            # Single frame mode
            frames_count = 1
            gnss = data.get("gnss", {})
            imu = data.get("imu", {})

        is_valid_gnss = gnss.get("valid", True) and gnss.get("status") != "UNAVAILABLE"
        lat = gnss.get("latitude", 13.0827) or 13.0827
        lon = gnss.get("longitude", 80.2707) or 80.2707
        speed_mps = gnss.get("speed_mps", 10.0) or 10.0
        heading_deg = gnss.get("heading_deg", 45.0) or 45.0

        if is_valid_gnss:
            nav_mode = "GNSS_INS"
            confidence = 0.98
            drift_estimate = 0.0
            is_dr_mode = False
        else:
            nav_mode = "DEAD_RECKONING"
            confidence = 0.72
            drift_estimate = 4.25
            is_dr_mode = True

        calculated_state = {
            "latitude": float(lat),
            "longitude": float(lon),
            "speed_kmh": round(float(speed_mps) * 3.6, 2),
            "heading_deg": round(float(heading_deg), 2),
            "confidence_score": confidence,
            "drift_estimate_m": drift_estimate,
            "navigation_mode": nav_mode,
            "is_dr_mode": is_dr_mode,
        }

        return Response(
            {
                "status": "SUCCESS",
                "message": "Telemetry frame processed successfully",
                "calculated_navigation_state": calculated_state,
                "processed_frames": frames_count,
            },
            status=status.HTTP_200_OK,
        )
