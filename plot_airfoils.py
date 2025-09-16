import os
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_2D_FILE = "airfoil_polars.csv"
RESULTS_COMPARISON_FILE = "airfoil_comparison.csv"
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


def plot_2d():
    """Plot 2D polars for each airfoil individually."""
    df = safe_read_csv(RESULTS_2D_FILE)
    if df.empty or "Airfoil" not in df.columns:
        print("⚠️ No valid 2D polar data to plot.")
        return

    for airfoil in df["Airfoil"].unique():
        airfoil_df = df[df["Airfoil"] == airfoil]

        plt.figure(figsize=(9, 6))
        plt.plot(airfoil_df["Alpha"], airfoil_df["CL"], label="CL", marker="o")
        plt.plot(airfoil_df["Alpha"], airfoil_df["CD"], label="CD", marker="s")
        plt.plot(airfoil_df["Alpha"], airfoil_df["CM"], label="CM", marker="^")

        plt.title(f"{airfoil} - Polar Curves")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("Coefficient")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(OUTPUT_DIR, f"{airfoil}_polar.png"))
        plt.close()


def plot_comparison():
    """Compare L/D ratios across airfoils."""
    df = safe_read_csv(RESULTS_COMPARISON_FILE)
    if df.empty or "Airfoil" not in df.columns:
        print("⚠️ No valid comparison data to plot.")
        return

    plt.figure(figsize=(10, 6))
    for airfoil in df["Airfoil"].unique():
        airfoil_df = df[df["Airfoil"] == airfoil]
        plt.plot(
            airfoil_df["Alpha"],
            airfoil_df["CL"] / airfoil_df["CD"],
            label=airfoil,
            marker="o"
        )

    plt.title("Lift-to-Drag Ratio Comparison")
    plt.xlabel("Angle of Attack (deg)")
    plt.ylabel("L/D Ratio")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, "airfoil_comparison.png"))
    plt.close()


def plot_results():
    """Generate all plots."""
    plot_2d()
    plot_comparison()
    print(f"✅ Plots (if any) saved in {OUTPUT_DIR}/")


if __name__ == "__main__":
    plot_results()
