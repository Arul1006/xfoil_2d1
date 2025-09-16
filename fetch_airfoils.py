# fetch_airfoils.py
import os
import requests
from typing import List

UIUC_BASE = "https://m-selig.ae.illinois.edu/ads/coord/"
AIRFOIL_DIR = "airfoils"

def fetch_airfoils(airfoil_list: List[str]) -> list:
    """
    Fetch .dat files from UIUC into ./airfoils.
    Skips any that already exist.
    Returns list of file paths successfully available (downloaded or cached).
    """
    os.makedirs(AIRFOIL_DIR, exist_ok=True)
    fetched_files = []

    for name in airfoil_list:
        file_path = os.path.join(AIRFOIL_DIR, f"{name}.dat")
        if os.path.exists(file_path):
            print(f"📂 {name}.dat already exists. Skipping download.")
            fetched_files.append(file_path)
            continue

        url = f"{UIUC_BASE}{name}.dat"
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch {name} from UIUC: {e}")
            continue

        with open(file_path, "w", newline="\n") as f:
            f.write(r.text)
        print(f"✅ Downloaded {name} → {file_path}")
        fetched_files.append(file_path)

    return fetched_files

if __name__ == "__main__":
    # quick smoke test
    airfoils = ["naca2412", "s1223", "e423", "sd7037", "s3021", "ag35", "naca23012", "naca4415"]
    files = fetch_airfoils(airfoils)
    print("\nReady:", files)
