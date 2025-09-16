# plot_airfoils.py
import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_2D_FILE = "airfoil_polars.csv"
RESULTS_3D_FILE = "airfoil_3d_results.csv"

def plot_2d():
    if not os.path.exists(RESULTS_2D_FILE):
        print(f"⚠️ Skipping 2D plots: {RESULTS_2D_FILE} not found.")
        return

    try:
        df = pd.read_csv(RESULTS_2D_FILE)
    except pd.errors.EmptyDataError:
        print(f"⚠️ Skipping 2D plots: {RESULTS_2D_FILE} is empty.")
        return

    if df.empty:
        print("⚠️ Skipping 2D plots: data frame is empty.")
        return

    # Ensure column name case compatibility (accept both CL or Cl)
    # Normalize column names to expected ones if needed
    cols = {c.lower(): c for c in df.columns}
    # Accept both CL/CD/CM or Cl/Cd/Cm
    if "cl" in cols and "cd" in cols and "cm" in cols:
        df = df.rename(columns={cols["cl"]: "CL", cols["cd"]: "CD", cols["cm"]: "CM"})
    # Some older scripts might use small-case column names; ensure Re and Alpha also exist
    if "re" in cols and "re" not in df.columns:
        # nothing to do — handled above

    # —— CL vs Alpha per airfoil (at a few Re samples)
    plt.figure(figsize=(9,6))
    for airfoil in df["Airfoil"].unique():
        dfa = df[df["Airfoil"] == airfoil]
        for Re in dfa["Re"].quantile([0.0, 0.5, 1.0]).unique():
            sub = dfa[dfa["Re"] == Re].sort_values("Alpha")
            if sub.empty: continue
            plt.plot(sub["Alpha"], sub["CL"], label=f"{airfoil} @ Re={int(Re):,}")
    plt.xlabel("Alpha [deg]"); plt.ylabel("CL"); plt.title("CL vs Alpha")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout(); plt.savefig("Cl_vs_Alpha.png", dpi=300)
    plt.show()

    # —— Drag polar: CD vs CL
    plt.figure(figsize=(9,6))
    for airfoil in df["Airfoil"].unique():
        sub = df[df["Airfoil"] == airfoil].sort_values("CL")
        if sub.empty: continue
        plt.plot(sub["CL"], sub["CD"], label=airfoil)
    plt.xlabel("CL"); plt.ylabel("CD"); plt.title("Drag Polar (2D)")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout(); plt.savefig("Cd_vs_Cl_2D.png", dpi=300)
    plt.show()

    # —— CM vs Alpha
    plt.figure(figsize=(9,6))
    for airfoil in df["Airfoil"].unique():
        sub = df[df["Airfoil"] == airfoil].sort_values("Alpha")
        if sub.empty: continue
        plt.plot(sub["Alpha"], sub["CM"], label=airfoil)
    plt.xlabel("Alpha [deg]"); plt.ylabel("CM"); plt.title("CM vs Alpha (2D)")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout(); plt.savefig("Cm_vs_Alpha_2D.png", dpi=300)
    plt.show()


def plot_3d():
    if not os.path.exists(RESULTS_3D_FILE):
        print(f"⚠️ Skipping 3D plots: {RESULTS_3D_FILE} not found.")
        return

    try:
        df = pd.read_csv(RESULTS_3D_FILE)
    except pd.errors.EmptyDataError:
        print(f"⚠️ Skipping 3D plots: {RESULTS_3D_FILE} is empty.")
        return

    if df.empty:
        print("⚠️ Skipping 3D plots: data frame is empty.")
        return

    # —— CL vs alpha_trim grouped by airfoil (fix geometry to one combo for clarity)
    plt.figure(figsize=(9,6))
    for airfoil in df["Airfoil"].unique():
        dfa = df[df["Airfoil"] == airfoil]
        if dfa.empty: continue
        sel = dfa.sort_values(["b","c_root","taper","twist_tip_deg"]).groupby("alpha_trim_deg").head(1)
        sel = sel.sort_values("alpha_trim_deg")
        plt.plot(sel["alpha_trim_deg"], sel["CL"], label=airfoil)
    plt.xlabel("Trim Alpha [deg]"); plt.ylabel("CL"); plt.title("3D CL vs Trim Alpha")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout(); plt.savefig("CL_vs_AlphaTrim_3D.png", dpi=300)
    plt.show()

    # —— CD vs CL (3D)
    plt.figure(figsize=(9,6))
    for airfoil in df["Airfoil"].unique():
        sub = df[df["Airfoil"] == airfoil].sort_values("CL")
        if sub.empty: continue
        plt.plot(sub["CL"], sub["CD"], ".", label=airfoil, alpha=0.6)
    plt.xlabel("CL"); plt.ylabel("CD"); plt.title("3D Drag Polar (DOE cloud)")
    plt.grid(True, alpha=0.3); plt.legend(); plt.tight_layout(); plt.savefig("CD_vs_CL_3D.png", dpi=300)
    plt.show()


def plot_results():
    plot_2d()
    plot_3d()

if __name__ == "__main__":
    plot_results()
