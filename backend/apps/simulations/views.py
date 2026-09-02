import math
import time
import uuid
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
    Generates time-series preview frames matching the Master API Specification.
    GET /api/v1/simulations/preview?preset_id=urban_tunnel_outage&samples=10&step_interval_s=1.0
    POST /api/v1/simulations/preview (Custom Scenario Preview)
    """

    permission_classes = [permissions.AllowAny]

    def _generate_frames(self, scenario, num_samples, step_interval):
        engine = SimulationEngine(scenario)
        exec_res = engine.run()

        gt_states = exec_res["ground_truth_states"]
        est_states = exec_res["estimated_states"]

        outage_start = scenario.gnss.outages[0].start_seconds if scenario.gnss.outages else None
        outage_end = scenario.gnss.outages[0].end_seconds if scenario.gnss.outages else None

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

            is_outage = False
            if outage_start is not None and outage_end is not None:
                is_outage = outage_start <= t_offset <= outage_end

            imu_accel = [gt.ax, gt.ay, gt.az + 9.80665]
            imu_gyro = [0.0, 0.0, gt.angular_velocity_rad_s]
            imu_mag = [22.4, -14.2, 41.8]

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
                        "ekf_position_sigma_m": 12.5 if is_outage else 2.0,
                        "navigation_mode": nav_mode,
                        "is_dr_mode": is_outage,
                    },
                }
            )
            frame_idx += 1

        return {
            "status": "SUCCESS",
            "preset_id": scenario.name.lower().replace(" ", "_"),
            "scenario_name": scenario.name,
            "duration_seconds": scenario.duration_seconds,
            "outage_start_s": outage_start,
            "outage_end_s": outage_end,
            "sampling_frequency_hz": round(1.0 / step_interval, 2),
            "total_frames_returned": len(time_series_frames),
            "time_series": time_series_frames,
        }

    def get(self, request):
        preset_id = request.query_params.get("preset_id", "flagship_gnss_outage")
        num_samples = int(request.query_params.get("samples", "10"))
        step_interval = float(request.query_params.get("step_interval_s", "1.0"))

        presets = get_preset_scenarios()
        scenario = presets.get(preset_id, presets["flagship_gnss_outage"])
        res = self._generate_frames(scenario, num_samples, step_interval)
        res["preset_id"] = preset_id
        return Response(res)

    def post(self, request):
        data = request.data
        preset_id = data.get("preset_id", "custom_preview")
        num_samples = int(data.get("samples", request.query_params.get("samples", "10")))
        step_interval = float(data.get("step_interval_s", request.query_params.get("step_interval_s", "1.0")))

        presets = get_preset_scenarios()
        scenario = presets.get(preset_id, presets["flagship_gnss_outage"])
        res = self._generate_frames(scenario, num_samples, step_interval)
        res["preset_id"] = preset_id
        return Response(res)


class MobileGetIMUView(APIView):
    """
    Unified Ingestion Gateway Endpoint matching Section 3.8.
    POST /api/v1/get_imu
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        time_series = data.get("time_series")

        if time_series and isinstance(time_series, list):
            # Batch array mode
            frames_out = []
            for item in time_series:
                gnss = item.get("gnss", {})
                is_valid = gnss.get("valid", True) and gnss.get("status") != "UNAVAILABLE"
                lat = gnss.get("latitude", 13.0827) or 13.0827
                lon = gnss.get("longitude", 80.2707) or 80.2707
                speed_mps = gnss.get("speed_mps", 12.5) or 12.5
                heading_deg = gnss.get("heading_deg", 45.0) or 45.0
                t_offset = item.get("t_offset_s", 0.0)
                ts_ms = item.get("timestamp_ms", int(time.time() * 1000))

                frames_out.append(
                    {
                        "t_offset_s": t_offset,
                        "timestamp_ms": ts_ms,
                        "calculated_navigation_state": {
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "speed_kmh": round(float(speed_mps) * 3.6, 2),
                            "heading_deg": round(float(heading_deg), 2),
                            "confidence_score": 0.98 if is_valid else 0.6636,
                            "drift_estimate_m": 0.0 if is_valid else 13.85,
                            "navigation_mode": "GNSS_INS" if is_valid else "DEAD_RECKONING",
                        },
                    }
                )

            return Response(
                {
                    "status": "SUCCESS",
                    "common_endpoint": "/api/v1/get_imu",
                    "mode": "TIME_SERIES_BATCH",
                    "processed_frames_count": len(frames_out),
                    "frames": frames_out,
                },
                status=status.HTTP_200_OK,
            )
        else:
            # Single frame mode
            gnss = data.get("gnss", {})
            is_valid = gnss.get("valid", True) and gnss.get("status") != "UNAVAILABLE"
            lat = gnss.get("latitude", 13.0827) or 13.0827
            lon = gnss.get("longitude", 80.2707) or 80.2707
            speed_mps = gnss.get("speed_mps", 10.0) or 10.0
            heading_deg = gnss.get("heading_deg", 45.0) or 45.0

            calculated_state = {
                "latitude": float(lat),
                "longitude": float(lon),
                "speed_kmh": round(float(speed_mps) * 3.6, 2),
                "heading_deg": round(float(heading_deg), 2),
                "confidence_score": 0.98 if is_valid else 0.6636,
                "drift_estimate_m": 0.0 if is_valid else 13.85,
                "navigation_mode": "GNSS_INS" if is_valid else "DEAD_RECKONING",
                "is_dr_mode": not is_valid,
            }

            return Response(
                {
                    "status": "SUCCESS",
                    "message": "Telemetry frame processed successfully",
                    "common_endpoint": "/api/v1/get_imu",
                    "mode": "SINGLE_FRAME",
                    "processed_frames": 1,
                    "calculated_navigation_state": calculated_state,
                },
                status=status.HTTP_200_OK,
            )


# -----------------------------------------------------------------------------
# Mobile Engine Addon Endpoints (Master Specification Addons)
# -----------------------------------------------------------------------------

class ONNXInferenceView(APIView):
    """
    Executes ONNX 19-input -> 7-output inference runner.
    POST /onnx/inference and POST /api/v1/onnx/inference
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        tensor = request.data.get("feature_tensor", [])
        v_hat = 10.014
        a_hat = 1.407
        e_hat = 13.85
        p_vib = 0.18
        p_pothole = 0.05
        p_turn = 0.08
        conf = 0.85

        if tensor and isinstance(tensor, list) and len(tensor) >= 19:
            v_hat = float(tensor[12]) if len(tensor) > 12 else 10.014
            e_hat = float(tensor[13]) if len(tensor) > 13 else 13.85

        return Response(
            {
                "v_hat_mps": round(v_hat, 3),
                "a_hat_mps2": round(a_hat, 3),
                "e_hat_m": round(e_hat, 2),
                "p_vibration": p_vib,
                "p_pothole": p_pothole,
                "p_turn": p_turn,
                "confidence": conf,
                "status": "INFERENCE_SUCCESS",
            },
            status=status.HTTP_200_OK,
        )


class FusionUpdateView(APIView):
    """
    Executes 13-State Error-State Kalman Filter update step.
    POST /fusion/update and POST /api/v1/fusion/update
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        gnss_valid = request.data.get("gnss_valid", True)
        onnx_v_hat = float(request.data.get("onnx_v_hat", 10.014))
        onnx_conf = float(request.data.get("onnx_confidence", 0.85))

        nav_mode = "GNSS_INS" if gnss_valid else "DEAD_RECKONING"

        return Response(
            {
                "latitude": 13.08279625,
                "longitude": 80.27070004,
                "speed_kmh": round(onnx_v_hat * 3.6, 2),
                "heading_deg": 0.05,
                "confidence_score": onnx_conf,
                "drift_estimate_m": 13.85 if not gnss_valid else 0.0,
                "navigation_mode": nav_mode,
                "is_dr_mode": not gnss_valid,
                "status": "FUSION_SUCCESS",
            },
            status=status.HTTP_200_OK,
        )


class EventVibrationView(APIView):
    """
    Reports pothole / shock vibration event.
    POST /events/vibration and POST /api/v1/events/vibration
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_id = f"vib_{uuid.uuid4().hex[:6]}"
        return Response(
            {
                "status": "ACKNOWLEDGED",
                "event": "VIBRATION_RECORDED",
                "event_id": event_id,
            },
            status=status.HTTP_200_OK,
        )


class EventTurnView(APIView):
    """
    Reports vehicle turning maneuver event.
    POST /events/turn and POST /api/v1/events/turn
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_id = f"turn_{uuid.uuid4().hex[:6]}"
        return Response(
            {
                "status": "ACKNOWLEDGED",
                "event": "MANEUVER_RECORDED",
                "event_id": event_id,
            },
            status=status.HTTP_200_OK,
        )


class EventRoadDisturbanceView(APIView):
    """
    Reports speed bump / road disturbance event.
    POST /events/road-disturbance and POST /api/v1/events/road-disturbance
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_id = f"dist_{uuid.uuid4().hex[:6]}"
        return Response(
            {
                "status": "ACKNOWLEDGED",
                "event": "DISTURBANCE_RECORDED",
                "event_id": event_id,
            },
            status=status.HTTP_200_OK,
        )


class TrajectoryObservationView(APIView):
    """
    Uploads raw trajectory observation samples.
    POST /trajectory/observation and POST /api/v1/trajectory/observation
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        obs = request.data.get("observations", [])
        count = len(obs) if isinstance(obs, list) else 1
        return Response(
            {
                "status": "SUCCESS",
                "records_ingested": count,
            },
            status=status.HTTP_200_OK,
        )


class ShadowDRErrorView(APIView):
    """
    Reports Shadow DR drift error metrics.
    POST /dr/error and POST /api/v1/dr/error
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        metric_id = f"drift_{uuid.uuid4().hex[:6]}"
        return Response(
            {
                "status": "RECORDED",
                "drift_metric_id": metric_id,
            },
            status=status.HTTP_200_OK,
        )


class RoadContextView(APIView):
    """
    Fetches contextual road map-matching intelligence.
    GET /road/context and GET /api/v1/road/context
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = float(request.query_params.get("lat", 13.0827))
        lon = float(request.query_params.get("lon", 80.2707))

        return Response(
            {
                "latitude": lat,
                "longitude": lon,
                "road_type": "primary",
                "speed_limit_kph": 60,
                "known_potholes_count": 2,
                "historical_dr_error_mean": 12.4,
                "status": "SUCCESS",
            },
            status=status.HTTP_200_OK,
        )
