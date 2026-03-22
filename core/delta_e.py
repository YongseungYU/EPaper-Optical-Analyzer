"""Delta E calculation functions (CIE76, CIE94, CIEDE2000)."""

from __future__ import annotations

import math
from typing import Tuple, Dict

import pandas as pd


def delta_e_cie76(
    L1: float, a1: float, b1: float,
    L2: float, a2: float, b2: float,
) -> float:
    """Calculate Delta E using CIE76 formula (simple Euclidean)."""
    return math.sqrt((L1 - L2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2)


def delta_e_cie94(
    L1: float, a1: float, b1: float,
    L2: float, a2: float, b2: float,
    *,
    textile: bool = False,
) -> float:
    """Calculate Delta E using CIE94 formula."""
    dL = L1 - L2
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    dC = C1 - C2
    da = a1 - a2
    db = b1 - b2
    dH_sq = da**2 + db**2 - dC**2
    dH_sq = max(dH_sq, 0.0)

    if textile:
        kL, K1, K2 = 2.0, 0.048, 0.014
    else:
        kL, K1, K2 = 1.0, 0.045, 0.015

    SL = 1.0
    SC = 1.0 + K1 * C1
    SH = 1.0 + K2 * C1

    term_L = dL / (kL * SL)
    term_C = dC / SC
    term_H = math.sqrt(dH_sq) / SH

    return math.sqrt(term_L**2 + term_C**2 + term_H**2)


def delta_e_ciede2000(
    L1: float, a1: float, b1: float,
    L2: float, a2: float, b2: float,
    *,
    kL: float = 1.0,
    kC: float = 1.0,
    kH: float = 1.0,
) -> float:
    """Calculate Delta E using CIEDE2000 formula."""
    # Step 1
    C1ab = math.sqrt(a1**2 + b1**2)
    C2ab = math.sqrt(a2**2 + b2**2)
    Cab_mean = (C1ab + C2ab) / 2.0
    Cab_mean_7 = Cab_mean**7
    G = 0.5 * (1.0 - math.sqrt(Cab_mean_7 / (Cab_mean_7 + 25.0**7)))

    a1p = a1 * (1.0 + G)
    a2p = a2 * (1.0 + G)

    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)

    h1p = math.degrees(math.atan2(b1, a1p)) % 360.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360.0

    # Step 2
    dLp = L2 - L1
    dCp = C2p - C1p

    if C1p * C2p == 0.0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180.0:
        dhp = h2p - h1p
    elif h2p - h1p > 180.0:
        dhp = h2p - h1p - 360.0
    else:
        dhp = h2p - h1p + 360.0

    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2.0))

    # Step 3
    Lp_mean = (L1 + L2) / 2.0
    Cp_mean = (C1p + C2p) / 2.0

    if C1p * C2p == 0.0:
        hp_mean = h1p + h2p
    elif abs(h1p - h2p) <= 180.0:
        hp_mean = (h1p + h2p) / 2.0
    elif h1p + h2p < 360.0:
        hp_mean = (h1p + h2p + 360.0) / 2.0
    else:
        hp_mean = (h1p + h2p - 360.0) / 2.0

    T = (
        1.0
        - 0.17 * math.cos(math.radians(hp_mean - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * hp_mean))
        + 0.32 * math.cos(math.radians(3.0 * hp_mean + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * hp_mean - 63.0))
    )

    SL = 1.0 + 0.015 * (Lp_mean - 50.0) ** 2 / math.sqrt(20.0 + (Lp_mean - 50.0) ** 2)
    SC = 1.0 + 0.045 * Cp_mean
    SH = 1.0 + 0.015 * Cp_mean * T

    Cp_mean_7 = Cp_mean**7
    RC = 2.0 * math.sqrt(Cp_mean_7 / (Cp_mean_7 + 25.0**7))
    d_theta = 30.0 * math.exp(-((hp_mean - 275.0) / 25.0) ** 2)
    RT = -math.sin(math.radians(2.0 * d_theta)) * RC

    result = math.sqrt(
        (dLp / (kL * SL)) ** 2
        + (dCp / (kC * SC)) ** 2
        + (dHp / (kH * SH)) ** 2
        + RT * (dCp / (kC * SC)) * (dHp / (kH * SH))
    )
    return result


def batch_delta_e(
    measured: pd.DataFrame,
    reference: Dict[str, Tuple[float, float, float]],
    formula: str = "CIEDE2000",
) -> pd.DataFrame:
    """Calculate Delta E for multiple samples against reference values.

    Parameters
    ----------
    measured : pd.DataFrame
        Must contain columns: SAMPLE_NAME (or SAMPLE_ID), LAB_L, LAB_A, LAB_B.
    reference : dict
        Mapping of sample name -> (L*, a*, b*) reference values.
    formula : str
        One of 'CIE76', 'CIE94', 'CIEDE2000'.

    Returns
    -------
    pd.DataFrame
        Results with columns for measured, reference, and Delta E values.
    """
    func_map = {
        "CIE76": delta_e_cie76,
        "CIE94": delta_e_cie94,
        "CIEDE2000": delta_e_ciede2000,
    }
    calc_fn = func_map.get(formula, delta_e_ciede2000)

    name_col = "SAMPLE_NAME" if "SAMPLE_NAME" in measured.columns else "SAMPLE_ID"

    results = []
    for _, row in measured.iterrows():
        name = str(row.get(name_col, ""))
        mL, ma, mb = float(row["LAB_L"]), float(row["LAB_A"]), float(row["LAB_B"])

        if name in reference:
            rL, ra, rb = reference[name]
        else:
            continue

        de = calc_fn(mL, ma, mb, rL, ra, rb)
        results.append({
            "sample_name": name,
            "measured_L": mL,
            "measured_a": ma,
            "measured_b": mb,
            "reference_L": rL,
            "reference_a": ra,
            "reference_b": rb,
            "delta_e": round(de, 4),
        })

    return pd.DataFrame(results)
