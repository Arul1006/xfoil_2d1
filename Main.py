# Main.py
from fetch_airfoils import fetch_airfoils
from analyze_airfoils import analyze_airfoils
from analyze_3d import analyze_3d
from plot_airfoils import plot_results

if __name__ == "__main__":
    # Pick your airfoils here (names must exist on UIUC)
    airfoils = [
        "naca2412", "s1223", "e423", "sd7037", "s3021",
        "ag35", "naca23012", "naca4415"
    ]

    # 1) Fetch (cached)
    fetch_airfoils(airfoils)

    # 2) 2D batch analysis → unified CSV
    analyze_airfoils(airfoils)

    # 3) 3D DOE using section polars → CSV
    analyze_3d()

    # 4) Figures
    plot_results()

    print("\n✅ Pipeline complete.")
