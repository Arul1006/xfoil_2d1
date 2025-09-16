# analyze_3d.py
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

RESULTS_2D_FILE = Path("airfoil_polars.csv")
RESULTS_3D_FILE = Path("airfoil_3d_results.csv")

# Atmosphere / flight setup (edit as needed)
RHO = 1.225    # kg/m^3
MU  = 1.81e-5  # Pa·s
VEL = 20.0     # m/s
q    = 0.5 * RHO * VEL**2

# Geometry sweeps (edit as desired)
WINGSPANS = [0.5, 1.0, 2.0]        # meters (full span)
ROOT_CHORDS = [0.15, 0.20, 0.30]   # meters
TAPERS = [1.0, 0.8, 0.6]           # tip chord / root chord
DIHEDRALS = [0.0, 5.0, 10.0]       # deg (kept for metadata)
TWIST_ROOTS = [0.0]                # deg
TWIST_TIPS = [-2.0, 0.0, +2.0]     # deg
TRIM_ALPHAS = [0.0, 2.0, 4.0]      # deg (aircraft AoA)

N_SPAN_SECTIONS = 31  # spanwise stations per semi-wing

def _interp_section(df: pd.DataFrame, airfoil: str, Re: float, alpha: float) -> Tuple[float, float, float]:
    sub = df[df["Airfoil"] == airfoil]
    if sub.empty:
        return (np.nan, np.nan, np.nan)

    # available Re values
    res = np.unique(sub["Re"].values)
    idx = np.searchsorted(res, Re)
    if idx == 0:
        Re_lo, Re_hi = res[0], res[min(1, len(res)-1)]
    elif idx >= len(res):
        if len(res) == 1:
            Re_lo = Re_hi = res[0]
        else:
            Re_lo, Re_hi = res[-2], res[-1]
    else:
        Re_lo, Re_hi = res[idx-1], res[idx]

    def interp_at(Rtarget):
        dfr = sub[sub["Re"] == Rtarget].sort_values("Alpha")
        if dfr.empty:
            return (np.nan, np.nan, np.nan)
        a = np.clip(alpha, dfr["Alpha"].min(), dfr["Alpha"].max())
        CL = float(np.interp(a, dfr["Alpha"].to_numpy(), dfr["CL"].to_numpy()))
        CD = float(np.interp(a, dfr["Alpha"].to_numpy(), dfr["CD"].to_numpy()))
        CM = float(np.interp(a, dfr["Alpha"].to_numpy(), dfr["CM"].to_numpy()))
        return (CL, CD, CM)

    CL_lo, CD_lo, CM_lo = interp_at(Re_lo)
    CL_hi, CD_hi, CM_hi = interp_at(Re_hi)

    if np.isnan([CL_lo, CD_lo, CM_lo]).all() and np.isnan([CL_hi, CD_hi, CM_hi]).all():
        return (np.nan, np.nan, np.nan)

    t = 0.0 if Re_hi == Re_lo else (Re - Re_lo) / (Re_hi - Re_lo + 1e-12)
    CL = (1 - t) * CL_lo + t * CL_hi
    CD = (1 - t) * CD_lo + t * CD_hi
    CM = (1 - t) * CM_lo + t * CM_hi
    return (float(CL), float(CD), float(CM))

def analyze_3d():
    if not RESULTS_2D_FILE.exists():
        print(f"❌ 2D results not found: {RESULTS_2D_FILE.resolve()}")
        return pd.DataFrame()

    try:
        df2 = pd.read_csv(RESULTS_2D_FILE)
    except pd.errors.EmptyDataError:
        print(f"❌ 2D CSV is empty: {RESULTS_2D_FILE.resolve()}")
        return pd.DataFrame()

    req = {"Airfoil", "Re", "Alpha", "CL", "CD", "CM"}
    if not req.issubset(set(df2.columns)):
        print(f"❌ 2D CSV missing required columns: {req - set(df2.columns)}")
        return pd.DataFrame()

    airfoils = sorted(df2["Airfoil"].unique())
    out_rows = []

    for airfoil in airfoils:
        for b in WINGSPANS:
            semi = b / 2.0
            for c_root in ROOT_CHORDS:
                for taper in TAPERS:
                    c_tip = c_root * taper
                    S = b * 0.5 * (c_root + c_tip)
                    AR = b**2 / S if S > 0 else np.nan
                    e = max(0.65, 1.78*(1 - 0.045 * AR**0.68) - 0.64) if np.isfinite(AR) else 0.8

                    y = np.linspace(0.0, semi, N_SPAN_SECTIONS)
                    chord_y = c_root + (c_tip - c_root) * (y / semi) if semi > 0 else np.full_like(y, c_root)

                    for dihedral in DIHEDRALS:
                        for twist_root in TWIST_ROOTS:
                            for twist_tip in TWIST_TIPS:
                                twist_y = twist_root + (twist_tip - twist_root) * (y / semi) if semi > 0 else np.zeros_like(y)

                                for alpha_trim in TRIM_ALPHAS:
                                    dy = semi / (N_SPAN_SECTIONS - 1) if N_SPAN_SECTIONS > 1 else semi
                                    dS = chord_y * dy

                                    alpha_local = alpha_trim + twist_y
                                    Re_local = (RHO * VEL * chord_y) / MU

                                    CL_sec = np.zeros_like(y)
                                    CD_sec = np.zeros_like(y)
                                    CM_sec = np.zeros_like(y)

                                    for i in range(len(y)):
                                        CL_i, CD_i, CM_i = _interp_section(df2, airfoil, float(Re_local[i]), float(alpha_local[i]))
                                        CL_sec[i] = CL_i
                                        CD_sec[i] = CD_i
                                        CM_sec[i] = CM_i

                                    L_semi = np.nansum(q * dS * CL_sec)
                                    Dp_semi = np.nansum(q * dS * CD_sec)

                                    L = 2.0 * L_semi
                                    Dp = 2.0 * Dp_semi

                                    CL = L / (q * S) if S > 0 else np.nan
                                    CDp = Dp / (q * S) if S > 0 else np.nan
                                    CDi = (CL**2) / (np.pi * AR * e) if (np.isfinite(AR) and AR > 0 and e > 0) else np.nan
                                    CD = CDp + CDi if (np.isfinite(CDp) and np.isfinite(CDi)) else np.nan

                                    c_mac = (2.0/3.0) * c_root * (1 + taper + taper**2) / (1 + taper) if (1 + taper) != 0 else np.nan
                                    Mq_semi = np.nansum((q * dS) * CM_sec * chord_y)
                                    M = 2.0 * Mq_semi
                                    Cm = M / (q * S * c_mac) if (S > 0 and np.isfinite(c_mac) and c_mac > 0) else np.nan

                                    out_rows.append({
                                        "Airfoil": airfoil,
                                        "b": b,
                                        "c_root": c_root,
                                        "taper": taper,
                                        "c_tip": c_tip,
                                        "S": S,
                                        "AR": AR,
                                        "dihedral_deg": dihedral,
                                        "twist_root_deg": twist_root,
                                        "twist_tip_deg": twist_tip,
                                        "alpha_trim_deg": alpha_trim,
                                        "V": VEL,
                                        "rho": RHO,
                                        "mu": MU,
                                        "CL": CL,
                                        "CDp": CDp,
                                        "CDi": CDi,
                                        "CD": CD,
                                        "Cm": Cm,
                                        "L_N": L,
                                    })

                                    print(f"✅ 3D: {airfoil} | b={b} c_root={c_root} taper={taper} "
                                          f"twist=({twist_root}->{twist_tip}) α={alpha_trim} → CL={np.nan_to_num(CL):.3f}, CD={np.nan_to_num(CD):.3f}")

    df3 = pd.DataFrame(out_rows)
    if df3.empty:
        print("⚠️ 3D: No rows generated; not writing CSV.")
        return df3

    df3 = df3.sort_values(["Airfoil", "b", "c_root", "taper", "alpha_trim_deg"]).reset_index(drop=True)
    df3.to_csv(RESULTS_3D_FILE, index=False)
    print(f"\n📊 Saved 3D DOE → {RESULTS_3D_FILE.resolve()}  ({len(df3)} rows)")
    return df3

if __name__ == "__main__":
    analyze_3d()
