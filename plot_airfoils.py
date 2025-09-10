import os
import pandas as pd
import matplotlib.pyplot as plt
import glob

OUTPUT_DIR = "plots"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_latest_results_file():
    """Find the most recent airfoil_polars file."""
    list_of_files = glob.glob('airfoil_polars_*.csv')
    if not list_of_files:
        print("❌ No airfoil_polars file found. Please run the analysis first.")
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


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
    """Generate all plots from the unified polar CSV."""
    results_file = get_latest_results_file()
    if results_file is None:
        return

    df = safe_read_csv(results_file)
    if df.empty or "airfoil" not in df.columns:
        print("⚠️ No valid 2D polar data to plot.")
        return

    # Plotting loop for each airfoil
    for airfoil in df["airfoil"].unique():
        airfoil_df = df[df["airfoil"] == airfoil]

        plt.figure(figsize=(9, 6))
        plt.plot(airfoil_df["alpha"], airfoil_df["CL"], label="CL", marker="o")
        plt.title(f"{airfoil} - Lift Coefficient")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("CL")
        plt.grid(True)
        plt.savefig(os.path.join(OUTPUT_DIR, f"{airfoil}_CL.png"))
        plt.close()

        plt.figure(figsize=(9, 6))
        plt.plot(airfoil_df["alpha"], airfoil_df["CD"], label="CD", marker="s")
        plt.title(f"{airfoil} - Drag Coefficient")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("CD")
        plt.grid(True)
        plt.savefig(os.path.join(OUTPUT_DIR, f"{airfoil}_CD.png"))
        plt.close()

        plt.figure(figsize=(9, 6))
        plt.plot(airfoil_df["alpha"], airfoil_df["CM"], label="CM", marker="^")
        plt.title(f"{airfoil} - Moment Coefficient")
        plt.xlabel("Angle of Attack (deg)")
        plt.ylabel("CM")
        plt.grid(True)
        plt.savefig(os.path.join(OUTPUT_DIR, f"{airfoil}_CM.png"))
        plt.close()

    plt.figure(figsize=(10, 6))
    for airfoil in df["airfoil"].unique():
        airfoil_df = df[df["airfoil"] == airfoil]
        plt.plot(airfoil_df["alpha"], airfoil_df["CL"], label=airfoil)
    plt.title("Lift Coefficient Comparison")
    plt.xlabel("Angle of Attack (deg)")
    plt.ylabel("CL")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, "CL_comparison.png"))
    plt.close()

    plt.figure(figsize=(10, 6))
    for airfoil in df["airfoil"].unique():
        airfoil_df = df[df["airfoil"] == airfoil]
        ld_ratio = airfoil_df["CL"] / airfoil_df["CD"].replace(0, float("nan"))
        plt.plot(airfoil_df["alpha"], ld_ratio, label=airfoil)
    plt.title("Lift-to-Drag Ratio Comparison")
    plt.xlabel("Angle of Attack (deg)")
    plt.ylabel("L/D Ratio")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, "LD_comparison.png"))
    plt.close()

    print(f"✅ Plots (if any) saved in {OUTPUT_DIR}/")


if __name__ == "__main__":
    plot_results()