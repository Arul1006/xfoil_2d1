import os
import shutil
import glob
import numpy as np
from fetch_airfoils import fetch_airfoils
from analyze_airfoils import analyze_airfoils
from analyze_3d import analyze_3d
#from analyze_single_point import batch_analyze_single_points # <-- New import
from plot_airfoils import plot_results

if __name__ == "__main__":
    params = {
        "airfoils": [
            "naca2412", "s1223", "e423"
            "ag35", "naca23012", "naca4415", "sd7037", "s3021",
        ],
        "reynolds": list(np.logspace(5, 7, num=10)),
        "alphas": list(range(-5, 5, 1)),
        "mach": 0.1,
        "wing_sweep": 15,
        "wing_aspect_ratio": 7,
        "wing_taper_ratio": 0.5,
    }

    for d in ["plots", "temp_xfoil_*"]:
        if os.path.isdir(d):
            shutil.rmtree(d)
    for f in glob.glob("*.csv"):
        os.remove(f)

    params["airfoils"] = list(dict.fromkeys(params["airfoils"]))

    # 1) Fetch (cached)
    airfoil_dict = fetch_airfoils(params["airfoils"])

    # 2) 2D batch analysis -> unified CSV
    analyze_airfoils(airfoil_dict, params)

    # 3) Single-point analysis for additional metrics
    # batch_analyze_single_points(airfoil_dict, params) # <-- New call

    # 4) 3D DOE using section polars -> CSV
    # analyze_3d(params)

    # 5) Figures
    # plot_results()

    print("\n✅ Pipeline complete.")