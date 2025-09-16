# analyze_airfoils.py
import os
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

# Try optional backends
try:
    import aerosandbox as asb
except Exception:
    asb = None

try:
    from pyxfoil import Xfoil as PyXfoil
except Exception:
    PyXfoil = None

# -------------------------------
# Configuration
# -------------------------------
AIRFOILS: List[str] = [
    "naca2412",
    "s1223",
    "e423",
    "sd7037",
    "s3021",
    "ag35",
    "naca23012",
    "naca4415",
]

RE_LIST = [2e5, 5e5, 1e6]
ALPHA_LIST = np.arange(-5.0, 15.0 + 0.5, 0.5)  # -5 to 15 in 0.5 deg steps

AIRFOIL_DIR = Path("airfoils")
OUTPUT_FILE = Path("airfoil_polars.csv")

# -------------------------------
# Helpers
# -------------------------------
def _load_uiuc_coords(dat_path: Path) -> Optional[np.ndarray]:
    try:
        coords = np.loadtxt(str(dat_path), skiprows=1)
        return coords
    except Exception:
        return None

def _init_asb_xfoil(name: str, coords: Optional[np.ndarray], Re: float):
    try:
        if asb is None:
            return None
        # Create Airfoil object either by coordinates or by name
        if coords is not None:
            af = asb.Airfoil(name=name, coordinates=coords)
        else:
            af = asb.Airfoil(name=name)
        xf = asb.XFoil(airfoil=af, Re=Re, mach=0.0, max_iter=200)
        # set common tuning knobs if present
        if hasattr(xf, "n_crit"):
            xf.n_crit = 9
        return xf
    except Exception:
        return None

def _init_pyxfoil(name: str, coords: Optional[np.ndarray], Re: float):
    try:
        if PyXfoil is None:
            return None
        xf = PyXfoil(name)
        if coords is not None:
            xf.airfoil = coords
        xf.Re = float(Re)
        # set knobs if available
        if hasattr(xf, "n_crit"):
            xf.n_crit = 9
        if hasattr(xf, "max_iter"):
            xf.max_iter = 200
        return xf
    except Exception:
        return None

def _try_sweep_with_aseq(xf, backend: str, alpha_start: float, alpha_end: float, step: float):
    """
    Attempt to run a single aseq sweep (alpha_start → alpha_end step).
    Returns arrays (CL_arr, CD_arr, CM_arr, alpha_arr) on success, else None.
    """
    try:
        if hasattr(xf, "aseq"):
            # aseq may return arrays/tuples in different formats depending on wrapper
            res = xf.aseq(alpha_start, alpha_end, step)
            # Many wrappers return tuple like (cl_array, cd_array, cm_array, cpmin_array, xtr_top, xtr_bot)
            # Or return arrays directly. Try to robustly extract first three arrays.
            if isinstance(res, (list, tuple)):
                # find three array-like items in res
                arrays = []
                for item in res:
                    if hasattr(item, "__len__") and not isinstance(item, str):
                        arrays.append(np.asarray(item))
                    if len(arrays) >= 3:
                        break
                if len(arrays) >= 3:
                    cl_arr, cd_arr, cm_arr = arrays[0], arrays[1], arrays[2]
                    # number of points
                    n = len(cl_arr)
                    alpha_arr = np.linspace(alpha_start, alpha_end, n)
                    return cl_arr, cd_arr, cm_arr, alpha_arr
            # If res is dict-like or other, try reading keys
            if hasattr(res, "get"):
                cl_arr = np.asarray(res.get("CL", res.get("Cl", [])))
                cd_arr = np.asarray(res.get("CD", res.get("Cd", [])))
                cm_arr = np.asarray(res.get("CM", res.get("Cm", [])))
                if cl_arr.size and cd_arr.size and cm_arr.size:
                    n = cl_arr.size
                    alpha_arr = np.linspace(alpha_start, alpha_end, n)
                    return cl_arr, cd_arr, cm_arr, alpha_arr
    except Exception:
        return None
    return None

def _single_alpha_call(xf, backend: str, alpha: float) -> Optional[Tuple[float,float,float]]:
    """
    Try several method names to compute a single alpha point.
    Returns (CL, CD, CM) or None.
    """
    try:
        # AeroSandbox variant
        if backend == "asb":
            if hasattr(xf, "alpha"):
                res = xf.alpha(alpha)
                if isinstance(res, (list, tuple, np.ndarray)):
                    return float(res[0]), float(res[1]), float(res[2])
            # fallback to a() if present
            if hasattr(xf, "a"):
                res = xf.a(alpha)
                if isinstance(res, (list, tuple, np.ndarray)):
                    return float(res[0]), float(res[1]), float(res[2])
        else:
            # pyxfoil or other wrappers
            if hasattr(xf, "alpha"):
                res = xf.alpha(alpha)
                if isinstance(res, (list, tuple, np.ndarray)):
                    return float(res[0]), float(res[1]), float(res[2])
            if hasattr(xf, "a"):
                res = xf.a(alpha)
                if isinstance(res, (list, tuple, np.ndarray)):
                    return float(res[0]), float(res[1]), float(res[2])
            if hasattr(xf, "aseq"):
                # do tiny sweep for this angle
                res = xf.aseq(alpha, alpha, 1e-6)
                # attempt extraction
                if isinstance(res, (list, tuple)):
                    arrays = []
                    for item in res:
                        if hasattr(item, "__len__") and not isinstance(item, str):
                            arrays.append(np.asarray(item))
                        if len(arrays) >= 3:
                            break
                    if len(arrays) >= 3:
                        return float(arrays[0][0]), float(arrays[1][0]), float(arrays[2][0])
    except Exception:
        return None
    return None

# -------------------------------
# Main analysis function
# -------------------------------
def analyze_airfoils():
    results = []

    AIRFOIL_DIR.mkdir(exist_ok=True)

    for name in AIRFOILS:
        dat_path = AIRFOIL_DIR / f"{name}.dat"
        if not dat_path.exists():
            print(f"⚠️ Skipping {name}: file not found at {dat_path}")
            continue

        coords = _load_uiuc_coords(dat_path)

        for Re in RE_LIST:
            # Try to init backend
            xf = _init_asb_xfoil(name, coords, Re)
            backend = "asb" if xf is not None else None
            if xf is None:
                xf = _init_pyxfoil(name, coords, Re)
                backend = "pyxfoil" if xf is not None else None

            if xf is None:
                print(f"❌ Failed to init any XFoil backend for {name} @ Re={Re:.0f}")
                continue

            # Try aseq sweep for whole alpha range if available
            sweep_res = _try_sweep_with_aseq(xf, backend, float(ALPHA_LIST[0]), float(ALPHA_LIST[-1]), float(ALPHA_LIST[1]-ALPHA_LIST[0]))
            if sweep_res is not None:
                cl_arr, cd_arr, cm_arr, alpha_arr = sweep_res
                for cl, cd, cm, a in zip(cl_arr, cd_arr, cm_arr, alpha_arr):
                    results.append({
                        "Airfoil": name,
                        "Re": float(Re),
                        "Alpha": float(a),
                        "CL": float(cl),
                        "CD": float(cd),
                        "CM": float(cm),
                    })
                print(f"✅ {name} @ Re={Re:.0f}: swept {len(alpha_arr)} alphas via aseq")
                continue

            # If aseq sweep not available or failed, do per-alpha calls with retries
            for alpha in ALPHA_LIST:
                out = _single_alpha_call(xf, backend, float(alpha))
                if out is None:
                    # Try small retries with adjusted settings
                    retried = False
                    try:
                        # try adjusting n_crit / max_iter (if supported) once
                        if hasattr(xf, "n_crit"):
                            old = getattr(xf, "n_crit")
                            try:
                                xf.n_crit = max(7, old - 1)
                            except Exception:
                                pass
                        if hasattr(xf, "max_iter"):
                            try:
                                xf.max_iter = max(100, int(getattr(xf, "max_iter", 200) * 2))
                            except Exception:
                                pass
                        out = _single_alpha_call(xf, backend, float(alpha))
                        retried = True
                    except Exception:
                        out = None

                if out is None:
                    print(f"⚠️ {name} Re={Re:.0f} Alpha={alpha:.1f}: XFoil call failed")
                    continue

                CL, CD, CM = out
                results.append({
                    "Airfoil": name,
                    "Re": float(Re),
                    "Alpha": float(alpha),
                    "CL": float(CL),
                    "CD": float(CD),
                    "CM": float(CM),
                })

    # Save results (always write a CSV file with headers to avoid downstream crashes)
    df = pd.DataFrame(results)
    # ensure consistent column order
    cols = ["Airfoil", "Re", "Alpha", "CL", "CD", "CM"]
    if df.empty:
        empty_df = pd.DataFrame(columns=cols)
        empty_df.to_csv(OUTPUT_FILE, index=False)
        print("⚠️ No data collected; wrote empty CSV with headers to avoid downstream errors.")
        return empty_df

    df = df[cols].sort_values(["Airfoil", "Re", "Alpha"]).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ 2D results saved → {OUTPUT_FILE.resolve()}  ({len(df)} rows)")
    return df

# Entry
if __name__ == "__main__":
    analyze_airfoils()
