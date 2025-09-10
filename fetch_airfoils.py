import os
import requests
from typing import List

AIRFOIL_DIR = "airfoils"
UIUC_BASE = "https://m-selig.ae.illinois.edu/ads/coord/"


def download_airfoil_dat(airfoil_name: str) -> str:
    """
    Downloads an airfoil .dat file from UIUC if not cached.
    Returns the local filepath.
    """
    os.makedirs(AIRFOIL_DIR, exist_ok=True)
    filename = f"{airfoil_name}.dat"
    filepath = os.path.join(AIRFOIL_DIR, filename)
    url = f"{UIUC_BASE}{filename}"

    if os.path.exists(filepath):
        print(f"📂 {filename} already exists. Skipping download.")
        return filepath

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, "w") as f:
            f.write(response.text)
        print(f"✅ Downloaded {filename} to {AIRFOIL_DIR}")
        return filepath
    except Exception as e:
        print(f"❌ Failed to fetch {filename}: {e}")
        return None


def fetch_airfoils(airfoil_list: List[str]) -> dict:
    """
    Fetch all airfoils and return a dict {name: path}.
    """
    airfoil_dict = {}
    for af_name in airfoil_list:
        af_path = download_airfoil_dat(af_name)
        if af_path is not None:
            airfoil_dict[af_name] = af_path
    return airfoil_dict


if __name__ == "__main__":
    airfoils = [
        "naca2412", "s1223", "e423", "sd7037", "s3021",
        "ag35", "naca23012", "naca4415"
    ]
    files = fetch_airfoils(airfoils)
    print("\nReady:", files)