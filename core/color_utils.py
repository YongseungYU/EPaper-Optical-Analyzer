"""Color utility functions for L*a*b* conversion and identification."""

from __future__ import annotations

import math
from typing import Tuple


# -- Standard color names mapped to L*a*b* values --

_STANDARD_COLORS: dict[str, Tuple[float, float, float]] = {
    "White": (100.0, 0.0, 0.0),
    "Black": (0.0, 0.0, 0.0),
    "Red": (53.23, 80.11, 67.22),
    "Green": (87.74, -86.18, 83.18),
    "Blue": (32.30, 79.20, -107.86),
    "Yellow": (97.14, -21.56, 94.48),
    "Cyan": (91.11, -48.09, -14.13),
    "Magenta": (60.32, 98.25, -60.83),
    "Orange": (74.93, 23.93, 78.95),
    "Gray": (53.59, 0.0, 0.0),
    "Dark Gray": (25.0, 0.0, 0.0),
    "Light Gray": (75.0, 0.0, 0.0),
}


def lab_to_xyz(L: float, a: float, b: float) -> Tuple[float, float, float]:
    """Convert CIE L*a*b* to XYZ (D65 illuminant)."""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    epsilon = 0.008856
    kappa = 903.3

    xr = fx**3 if fx**3 > epsilon else (116.0 * fx - 16.0) / kappa
    yr = ((L + 16.0) / 116.0) ** 3 if L > kappa * epsilon else L / kappa
    zr = fz**3 if fz**3 > epsilon else (116.0 * fz - 16.0) / kappa

    # D65 reference white
    Xn, Yn, Zn = 95.047, 100.0, 108.883
    return xr * Xn, yr * Yn, zr * Zn


def xyz_to_srgb(X: float, Y: float, Z: float) -> Tuple[int, int, int]:
    """Convert XYZ to sRGB (0-255), clamped."""
    x = X / 100.0
    y = Y / 100.0
    z = Z / 100.0

    r_lin = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g_lin = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b_lin = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    def gamma(c: float) -> float:
        if c <= 0.0031308:
            return 12.92 * c
        return 1.055 * (c ** (1.0 / 2.4)) - 0.055

    r = int(round(max(0.0, min(1.0, gamma(r_lin))) * 255))
    g = int(round(max(0.0, min(1.0, gamma(g_lin))) * 255))
    b = int(round(max(0.0, min(1.0, gamma(b_lin))) * 255))
    return r, g, b


def lab_to_hex(L: float, a: float, b: float) -> str:
    """Convert L*a*b* to hex color string (e.g. '#FF0000')."""
    X, Y, Z = lab_to_xyz(L, a, b)
    r, g, b_val = xyz_to_srgb(X, Y, Z)
    return f"#{r:02X}{g:02X}{b_val:02X}"


def lab_to_rgb(L: float, a: float, b: float) -> Tuple[int, int, int]:
    """Convert L*a*b* to sRGB tuple (0-255)."""
    X, Y, Z = lab_to_xyz(L, a, b)
    return xyz_to_srgb(X, Y, Z)


def calculate_chroma(a: float, b: float) -> float:
    """Calculate chroma C* from a* and b*."""
    return math.sqrt(a**2 + b**2)


def calculate_hue(a: float, b: float) -> float:
    """Calculate hue angle h deg from a* and b* (in degrees, 0-360)."""
    h = math.degrees(math.atan2(b, a))
    if h < 0:
        h += 360.0
    return h


def calculate_gamut_area(colors: list[tuple[float, float]]) -> float:
    """Calculate the gamut area in a*b* plane using the Shoelace formula.

    Parameters
    ----------
    colors : list of (a*, b*) tuples
        Points in a*b* plane, will be ordered by hue angle automatically.

    Returns
    -------
    float
        Area in a*b* units squared.
    """
    if len(colors) < 3:
        return 0.0

    # Sort by hue angle for proper polygon
    sorted_colors = sorted(colors, key=lambda p: math.atan2(p[1], p[0]))

    # Shoelace formula
    n = len(sorted_colors)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += sorted_colors[i][0] * sorted_colors[j][1]
        area -= sorted_colors[j][0] * sorted_colors[i][1]
    return abs(area) / 2.0


def get_color_name(L: float, a: float, b: float) -> str:
    """Return the nearest standard color name for given L*a*b* values.

    Uses simple Euclidean distance in L*a*b* space (CIE76).
    """
    min_dist = float("inf")
    best_name = "Unknown"
    for name, (Lr, ar, br) in _STANDARD_COLORS.items():
        dist = math.sqrt((L - Lr) ** 2 + (a - ar) ** 2 + (b - br) ** 2)
        if dist < min_dist:
            min_dist = dist
            best_name = name
    return best_name
