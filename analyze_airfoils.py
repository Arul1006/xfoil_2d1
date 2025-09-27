import subprocess
import tempfile
import os
import csv
import pandas as pd
import numpy as np

# Path to XFOIL executable in your PyCharm project folder
XFOIL_PATH = r"D:\Arul\PycharmProjects\AeroSandbox\xfoil.exe"

RESULTS_2D_FILE = "airfoil_polars.csv"
RESULTS_COMPARISON_FILE = "airfoil_comparison.csv"


def run_xfoil(airfoil, alphas, Re=1e6, Mach=0.0):
    """
    Runs XFOIL for a given airfoil and list of angles of attack.
    Returns a list of results.
    """
    polar_file = os.path.join(tempfile.gettempdir(), f"{airfoil}_polar.txt")

    # Build XFOIL command sequence
    commands = ""
    if airfoil.lower().startswith("naca"):
        commands += f"NACA {airfoil[4:]}\n"
    else:
        commands += f"LOAD airfoils/{airfoil}.dat\n"
        commands += "\n"  # confirm name

    commands += "PANE\n"
    commands += "OPER\n"
    commands += f"VISC {Re:.1f}\n"
    commands += f"MACH {Mach:.4f}\n"
    commands += "PACC\n"
    commands += f"{polar_file}\n\n"

    for alpha in alphas:
        commands += f"ALFA {alpha}\n"

    commands += "PACC\nQUIT\n"

    # Run XFOIL
    process = subprocess.Popen([XFOIL_PATH],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
    process.communicate(commands)

    # Parse results
    results = []
    if os.path.exists(polar_file):
        with open(polar_file, "r") as f:
            lines = f.readlines()
            for line in lines[12:]:  # skip header
                try:
                    alpha, cl, cd, cdp, cm, xtr1, xtr2 = map(float, line.split())
                    results.append({
                        "Airfoil": airfoil,
                        "Re": Re,
                        "Alpha": alpha,
                        "CL": cl,
                        "CD": cd,
                        "CDp": cdp,
                        "CM": cm,
                        "Xtr_top": xtr1,
                        "Xtr_bottom": xtr2,
                    })
                except:
                    continue
    return results


def analyze_airfoils(airfoils):
    """Run XFOIL on all airfoils and save unified CSV."""
    # New alpha range: -30° → 30° (step 1°)
    alphas = np.arange(-30, 30.5, 0.5).tolist()


    # Reynolds sweep: 30k → 3M with 200 steps (log-spaced for physics realism)
    Res = np.logspace(np.log10(3e4), np.log10(3e6), 200)

    all_results = []

    for airfoil in airfoils:
        print(f"\nAnalyzing {airfoil}...")
        for Re in Res:
            results = run_xfoil(airfoil, alphas, Re=Re, Mach=0.0)
            if results:
                all_results.extend(results)
                print(f"✅ {airfoil} @ Re={Re:.0f}: {len(results)} points")
            else:
                print(f"⚠️ {airfoil} @ Re={Re:.0f}: No data collected.")

    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(RESULTS_2D_FILE, index=False)
        print(f"\n📊 Saved unified polar data → {RESULTS_2D_FILE} ({len(df)} rows)")

        # Also save comparison file (alpha, L/D)
        df["LD"] = df["CL"] / df["CD"].replace(0, float("nan"))
        df_comp = df[["Airfoil", "Re", "Alpha", "CL", "CD", "CM", "LD"]]
        df_comp.to_csv(RESULTS_COMPARISON_FILE, index=False)
        print(f"📊 Saved comparison data → {RESULTS_COMPARISON_FILE}")
    else:
        # Write empty CSVs for downstream consistency
        pd.DataFrame(columns=["Airfoil", "Re", "Alpha", "CL", "CD", "CDp", "CM", "Xtr_top", "Xtr_bottom"]).to_csv(
            RESULTS_2D_FILE, index=False)
        pd.DataFrame(columns=["Airfoil", "Re", "Alpha", "CL", "CD", "CM", "LD"]).to_csv(RESULTS_COMPARISON_FILE, index=False)
        print("⚠️ No data collected; wrote empty CSVs to avoid downstream errors.")


if __name__ == "__main__":
    airfoils = ["naca2412", "naca4415", "s1223", "e423", "s3021", "ag35", "naca23012"]
    analyze_airfoils(airfoils)
