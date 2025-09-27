import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_2D_FILE = "airfoil_polars.csv"
OUTPUT_DIR = "plots"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_read_csv(filepath):
    """Read CSV safely, return empty DataFrame if missing or invalid."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(filepath)
        if df.empty or len(df.columns) == 0:
            print(f"⚠️ File {filepath} is empty. Skipping.")
            return pd.DataFrame()
        return df
    except Exception as e:
        print(f"⚠️ Failed to read {filepath}: {e}")
        return pd.DataFrame()


def plot_results():
    """Plot CL, CD, CM vs Alpha for each airfoil at Re closest to 700k.
       Also plot a comparison of L/D across airfoils."""
    df = safe_read_csv(RESULTS_2D_FILE)
    if df.empty or "Airfoil" not in df.columns:
        print("⚠️ No valid 2D polar data to plot.")
        return

    target_Re = 7e5
    ld_comparison = {}

    for airfoil in df["Airfoil"].unique():
        airfoil_df = df[df["Airfoil"] == airfoil]

        # Find Re closest to 700k
        unique_Res = airfoil_df["Re"].unique()
        closest_Re = min(unique_Res, key=lambda x: abs(x - target_Re))

        re_df = airfoil_df[airfoil_df["Re"] == closest_Re]

        if re_df.empty:
            print(f"⚠️ No data for {airfoil} near Re={target_Re}")
            continue

        # Save individual CL, CD, CM plots
        plt.figure(figsize=(9, 6))
        plt.plot(re_df["Alpha"], re_df["CL"], label="CL", marker="o", markersize=3)
        plt.plot(re_df["Alpha"], re_df["CD"], label="CD", marker="s", markersize=3)
        plt.plot(re_df["Alpha"], re_df["CM"], label="CM", marker="^", markersize=3)

        plt.title(f"{airfoil} @ Re ≈ {closest_Re:.0f}")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("Coefficient")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, f"{airfoil}_Re{int(closest_Re)}.png"))
        plt.close()

        # Store L/D data for comparison plot
        re_df = re_df.copy()
        re_df["LD"] = re_df["CL"] / re_df["CD"].replace(0, float("nan"))
        ld_comparison[airfoil] = re_df[["Alpha", "LD"]]

    # --- L/D comparison plot ---
    if ld_comparison:
        plt.figure(figsize=(10, 6))
        for airfoil, data in ld_comparison.items():
            plt.plot(data["Alpha"], data["LD"], label=airfoil)

        plt.title("Lift-to-Drag Ratio (L/D) Comparison @ Re ≈ 700k")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("L/D")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "LD_comparison.png"))
        plt.close()

    print(f"✅ Plots saved in {OUTPUT_DIR}/")


if __name__ == "__main__":
    plot_results()
