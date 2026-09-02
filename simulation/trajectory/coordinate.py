import math
from typing import Tuple

# WGS-84 Ellipsoid constants
WGS84_A = 6378137.0  # Semi-major axis in meters
WGS84_F = 1 / 298.257223563  # Flattening
WGS84_B = WGS84_A * (1 - WGS84_F)  # Semi-minor axis
WGS84_E2 = (WGS84_A**2 - WGS84_B**2) / (WGS84_A**2)  # First eccentricity squared


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> Tuple[float, float, float]:
    """Converts WGS-84 latitude, longitude, altitude to ECEF (X, Y, Z) in meters."""
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat_rad) ** 2)

    X = (N + alt_m) * math.cos(lat_rad) * math.cos(lon_rad)
    Y = (N + alt_m) * math.cos(lat_rad) * math.sin(lon_rad)
    Z = (N * (1 - WGS84_E2) + alt_m) * math.sin(lat_rad)

    return X, Y, Z


def ecef_to_geodetic(X: float, Y: float, Z: float) -> Tuple[float, float, float]:
    """Converts ECEF (X, Y, Z) in meters to WGS-84 (lat_deg, lon_deg, alt_m)."""
    p = math.sqrt(X**2 + Y**2)
    if p == 0:
        return 90.0 if Z > 0 else -90.0, 0.0, abs(Z) - WGS84_B

    lon_rad = math.atan2(Y, X)
    lat_rad = math.atan2(Z, p * (1 - WGS84_E2))

    for _ in range(5):  # Bowring iterative conversion
        N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat_rad) ** 2)
        alt_m = p / math.cos(lat_rad) - N
        lat_rad = math.atan2(Z, p * (1 - WGS84_E2 * (N / (N + alt_m))))

    N = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(lat_rad) ** 2)
    alt_m = p / math.cos(lat_rad) - N

    return math.degrees(lat_rad), math.degrees(lon_rad), alt_m


def ecef_to_enu(
    X: float, Y: float, Z: float, lat0_deg: float, lon0_deg: float, alt0_deg: float
) -> Tuple[float, float, float]:
    """Converts ECEF point (X, Y, Z) to ENU (East, North, Up) relative to reference origin."""
    X0, Y0, Z0 = geodetic_to_ecef(lat0_deg, lon0_deg, alt0_deg)
    dX = X - X0
    dY = Y - Y0
    dZ = Z - Z0

    lat0_rad = math.radians(lat0_deg)
    lon0_rad = math.radians(lon0_deg)

    east = -math.sin(lon0_rad) * dX + math.cos(lon0_rad) * dY
    north = (
        -math.sin(lat0_rad) * math.cos(lon0_rad) * dX
        - math.sin(lat0_rad) * math.sin(lon0_rad) * dY
        + math.cos(lat0_rad) * dZ
    )
    up = (
        math.cos(lat0_rad) * math.cos(lon0_rad) * dX
        + math.cos(lat0_rad) * math.sin(lon0_rad) * dY
        + math.sin(lat0_rad) * dZ
    )

    return east, north, up


def enu_to_geodetic(
    east: float, north: float, up: float, lat0_deg: float, lon0_deg: float, alt0_m: float
) -> Tuple[float, float, float]:
    """Converts local ENU offset (meters) relative to origin into WGS-84 (lat_deg, lon_deg, alt_m)."""
    X0, Y0, Z0 = geodetic_to_ecef(lat0_deg, lon0_deg, alt0_m)

    lat0_rad = math.radians(lat0_deg)
    lon0_rad = math.radians(lon0_deg)

    dX = -math.sin(lon0_rad) * east - math.sin(lat0_rad) * math.cos(lon0_rad) * north + math.cos(lat0_rad) * math.cos(lon0_rad) * up
    dY = math.cos(lon0_rad) * east - math.sin(lat0_rad) * math.sin(lon0_rad) * north + math.cos(lat0_rad) * math.sin(lon0_rad) * up
    dZ = math.cos(lat0_rad) * north + math.sin(lat0_rad) * up

    X = X0 + dX
    Y = Y0 + dY
    Z = Z0 + dZ

    return ecef_to_geodetic(X, Y, Z)
