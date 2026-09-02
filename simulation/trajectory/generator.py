import math
from typing import List

import numpy as np

from simulation.scenario.schema import MovementMode, SimulationScenario
from .coordinate import enu_to_geodetic
from .kinematics import GroundTruthState


class TrajectoryGenerator:
    """Generates a time-series of kinematically consistent GroundTruthState frames for a scenario."""

    def __init__(self, scenario: SimulationScenario):
        self.scenario = scenario
        self.dt = scenario.timestep_seconds
        self.duration = scenario.duration_seconds
        self.num_steps = int(round(self.duration / self.dt)) + 1
        self.ref_lat = scenario.initial_state.latitude
        self.ref_lon = scenario.initial_state.longitude
        self.ref_alt = scenario.initial_state.altitude

    def generate(self) -> List[GroundTruthState]:
        mode = self.scenario.movement_mode

        if mode == MovementMode.STRAIGHT or mode == MovementMode.CONSTANT_VELOCITY:
            return self._generate_straight()
        elif mode == MovementMode.ACCELERATION:
            return self._generate_acceleration()
        elif mode == MovementMode.STOP_AND_GO:
            return self._generate_stop_and_go()
        elif mode == MovementMode.CIRCULAR:
            return self._generate_circular()
        elif mode == MovementMode.TURN or mode == MovementMode.WAYPOINT_ROUTE:
            return self._generate_waypoint_route()
        else:
            return self._generate_straight()

    def _generate_straight(self) -> List[GroundTruthState]:
        states = []
        v0 = self.scenario.initial_state.velocity_mps
        if v0 == 0.0:
            v0 = 1.4  # Default 1.4 m/s walking speed if zero
        heading_deg = self.scenario.initial_state.heading_deg
        heading_rad = math.radians(heading_deg)

        vx = v0 * math.sin(heading_rad)
        vy = v0 * math.cos(heading_rad)

        x, y, z = 0.0, 0.0, 0.0

        for k in range(self.num_steps):
            t = k * self.dt
            lat, lon, alt = enu_to_geodetic(x, y, z, self.ref_lat, self.ref_lon, self.ref_alt)
            states.append(
                GroundTruthState(
                    timestamp=t,
                    x=x,
                    y=y,
                    z=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    ax=0.0,
                    ay=0.0,
                    az=0.0,
                    roll=0.0,
                    pitch=0.0,
                    yaw=heading_rad,
                    heading_deg=heading_deg,
                    angular_velocity_rad_s=0.0,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                )
            )
            x += vx * self.dt
            y += vy * self.dt

        return states

    def _generate_acceleration(self) -> List[GroundTruthState]:
        states = []
        v = self.scenario.initial_state.velocity_mps
        a = 1.0  # 1.0 m/s² constant acceleration
        heading_deg = self.scenario.initial_state.heading_deg
        heading_rad = math.radians(heading_deg)

        x, y, z = 0.0, 0.0, 0.0

        for k in range(self.num_steps):
            t = k * self.dt
            vx = v * math.sin(heading_rad)
            vy = v * math.cos(heading_rad)
            ax = a * math.sin(heading_rad)
            ay = a * math.cos(heading_rad)

            lat, lon, alt = enu_to_geodetic(x, y, z, self.ref_lat, self.ref_lon, self.ref_alt)
            states.append(
                GroundTruthState(
                    timestamp=t,
                    x=x,
                    y=y,
                    z=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    ax=ax,
                    ay=ay,
                    az=0.0,
                    roll=0.0,
                    pitch=0.0,
                    yaw=heading_rad,
                    heading_deg=heading_deg,
                    angular_velocity_rad_s=0.0,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                )
            )
            v += a * self.dt
            x += vx * self.dt + 0.5 * ax * (self.dt**2)
            y += vy * self.dt + 0.5 * ay * (self.dt**2)

        return states

    def _generate_stop_and_go(self) -> List[GroundTruthState]:
        states = []
        heading_deg = self.scenario.initial_state.heading_deg
        heading_rad = math.radians(heading_deg)

        x, y, z = 0.0, 0.0, 0.0

        for k in range(self.num_steps):
            t = k * self.dt
            # 15 second cycle: 10s moving at 1.5 m/s, 5s stationary
            cycle_time = t % 15.0
            if cycle_time < 10.0:
                speed = 1.5
                accel = 0.0
            else:
                speed = 0.0
                accel = 0.0

            vx = speed * math.sin(heading_rad)
            vy = speed * math.cos(heading_rad)

            lat, lon, alt = enu_to_geodetic(x, y, z, self.ref_lat, self.ref_lon, self.ref_alt)
            states.append(
                GroundTruthState(
                    timestamp=t,
                    x=x,
                    y=y,
                    z=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    ax=0.0,
                    ay=0.0,
                    az=0.0,
                    roll=0.0,
                    pitch=0.0,
                    yaw=heading_rad,
                    heading_deg=heading_deg,
                    angular_velocity_rad_s=0.0,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                )
            )
            x += vx * self.dt
            y += vy * self.dt

        return states

    def _generate_circular(self) -> List[GroundTruthState]:
        states = []
        radius = 50.0  # 50 meter turning radius
        speed = self.scenario.initial_state.velocity_mps or 5.0
        omega = speed / radius  # angular velocity rad/s

        for k in range(self.num_steps):
            t = k * self.dt
            angle = omega * t
            x = radius * math.sin(angle)
            y = radius * (1 - math.cos(angle))
            z = 0.0

            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)

            heading_rad = angle
            heading_deg = (math.degrees(heading_rad)) % 360.0

            lat, lon, alt = enu_to_geodetic(x, y, z, self.ref_lat, self.ref_lon, self.ref_alt)
            states.append(
                GroundTruthState(
                    timestamp=t,
                    x=x,
                    y=y,
                    z=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    ax=-omega * vy,
                    ay=omega * vx,
                    az=0.0,
                    roll=0.0,
                    pitch=0.0,
                    yaw=heading_rad,
                    heading_deg=heading_deg,
                    angular_velocity_rad_s=omega,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                )
            )

        return states

    def _generate_waypoint_route(self) -> List[GroundTruthState]:
        waypoints = self.scenario.waypoints
        if not waypoints or len(waypoints) < 2:
            waypoints = [[0.0, 0.0], [100.0, 0.0], [100.0, 200.0], [300.0, 200.0]]

        speed = self.scenario.initial_state.velocity_mps or 5.0

        # Calculate segment lengths
        segments = []
        total_dist = 0.0
        for i in range(len(waypoints) - 1):
            p1 = np.array(waypoints[i])
            p2 = np.array(waypoints[i + 1])
            dist = float(np.linalg.norm(p2 - p1))
            segments.append((p1, p2, dist))
            total_dist += dist

        states = []
        curr_segment_idx = 0
        curr_segment_dist = 0.0

        x, y, z = float(waypoints[0][0]), float(waypoints[0][1]), 0.0

        for k in range(self.num_steps):
            t = k * self.dt
            if curr_segment_idx < len(segments):
                p1, p2, seg_len = segments[curr_segment_idx]
                direction = (p2 - p1) / seg_len if seg_len > 0 else np.array([1.0, 0.0])

                heading_rad = math.atan2(direction[0], direction[1])
                heading_deg = (math.degrees(heading_rad)) % 360.0

                vx = speed * direction[0]
                vy = speed * direction[1]

                curr_segment_dist += speed * self.dt
                if curr_segment_dist >= seg_len:
                    curr_segment_dist = 0.0
                    curr_segment_idx += 1
                    if curr_segment_idx < len(segments):
                        x, y = float(segments[curr_segment_idx][0][0]), float(segments[curr_segment_idx][0][1])
            else:
                vx, vy = 0.0, 0.0
                heading_rad = 0.0
                heading_deg = 0.0

            lat, lon, alt = enu_to_geodetic(x, y, z, self.ref_lat, self.ref_lon, self.ref_alt)
            states.append(
                GroundTruthState(
                    timestamp=t,
                    x=x,
                    y=y,
                    z=z,
                    vx=vx,
                    vy=vy,
                    vz=0.0,
                    ax=0.0,
                    ay=0.0,
                    az=0.0,
                    roll=0.0,
                    pitch=0.0,
                    yaw=heading_rad,
                    heading_deg=heading_deg,
                    angular_velocity_rad_s=0.0,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                )
            )

            x += vx * self.dt
            y += vy * self.dt

        return states
