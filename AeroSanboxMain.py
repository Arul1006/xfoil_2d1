# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
#
# from pyxfoil import xfoil
# from airfoil_db.airfoil import Airfoil
#
# # Example airfoils
# airfoils = ["naca2412", "s1223", "e423", "sd7037", "s3021",
#             "ag35", "naca23012", "n63215b-il", "naca4415", "naca632-215"]
#
# airfoil_coords = {}
# for name in airfoils:
#     try:
#         # Create airfoil object (airfoil_input="naca" works for NACA, else "db")
#         af = Airfoil(name=name, airfoil_input="naca" if "naca" in name.lower() else "db")
#         coords = np.array(af.coordinates)
#         airfoil_coords[name] = coords
#         print(f"Fetched {name}")
#     except Exception as e:
#         print(f"Could not fetch {name}: {e}")
#
# # Reynolds numbers
# re_list = np.linspace(3e4, 3e6, 150)
# alpha_range = np.linspace(-5, 20, 50)
#
# results = []
#
# for name, coords in airfoil_coords.items():
#     xf = xfoil()
#     xf.airfoil = coords
#
#     for Re in re_list:
#         xf.Re = Re
#         try:
#             Cl, Cd, Cm = xf.alpha(alpha_range)
#             for i, alpha in enumerate(alpha_range):
#                 results.append({
#                     "airfoil": name,
#                     "Re": float(np.round(Re, 0)),
#                     "alpha": alpha,
#                     "Cl": Cl[i],
#                     "Cd": Cd[i],
#                     "Cm": Cm[i],
#                     "Cl/Cd": Cl[i] / Cd[i] if Cd[i] > 0 else np.nan,
#                     "Cl^(3/2)/Cd": (Cl[i] ** 1.5) / Cd[i] if Cd[i] > 0 else np.nan,
#                     "sqrt(Cl)": np.sqrt(Cl[i]) if Cl[i] > 0 else np.nan,
#                     "Cpmin": np.nan,
#                     "Xtr_top": np.nan,
#                     "Xtr_bot": np.nan
#                 })
#         except Exception as e:
#             print(f"XFOIL failed for {name} at Re={Re:.0f}: {e}")
#
# df = pd.DataFrame(results)
# print(df.head())
#
# # ------------------------------
# # Save to CSV
# # ------------------------------
# output_file = "airfoil_polar_results.csv"
# df.to_csv(output_file, index=False)
# print(f"\n✅ Results saved to {output_file}")
#
#
#
# print("\nDataFrame Info:")
# print(df.info())
# print(df.head())
#
# #------------------------------
# # Plot example: Cl vs Alpha for one airfoil
# #------------------------------
# airfoil_to_plot = "naca2412"
#
# if not df.empty and "airfoil" in df.columns:
#     subset = df[df["airfoil"] == airfoil_to_plot]
#
#     if not subset.empty:
#         plt.figure(figsize=(10, 6))
#         for Re in sorted(subset["Re"].unique())[:5]:
#             data = subset[subset["Re"] == Re]
#             plt.plot(data["alpha"], data["Cl"], label=f"Re={int(Re)}")
#
#         plt.xlabel("Angle of Attack (deg)")
#         plt.ylabel("Cl")
#         plt.title(f"Lift Curve for {airfoil_to_plot}")
#         plt.legend()
#         plt.grid(True)
#         plt.show()
#     else:
#         print(f"⚠️ No data found for {airfoil_to_plot}")
# else:
#     print("⚠️ No valid simulation results in DataFrame.")


import requests
import aerosandbox as asb
import aerosandbox.numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# === Config ===
UIUC_BASE = "https://m-selig.ae.illinois.edu/ads/coord/"
airfoil_list = [
    "naca2412", "s1223", "e423", "sd7037", "s3021",
    "ag35", "naca23012", "n63215b-il", "naca4415", "naca632-215"
]

alpha_range = np.linspace(-5, 15, 30)  # angle of attack sweep
Re = 2e5  # Reynolds number


# === Helper Function ===
def load_airfoil_from_uiuc(name: str):
    url = f"{UIUC_BASE}{name}.dat"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch {name} from UIUC: {e}")
        return None

    coords_text = response.text.strip().splitlines()
    coords = []
    for line in coords_text[1:]:
        try:
            x, y = map(float, line.split())
            coords.append((x, y))
        except:
            continue

    if not coords:
        print(f"⚠️ No coordinates found in {name}.dat")
        return None

    print(f"✅ Successfully fetched {name} from UIUC")
    return asb.Airfoil(name=name, coordinates=coords)


# === Run Batch Analysis ===
results = []
for name in airfoil_list:
    af = load_airfoil_from_uiuc(name)
    if af is None:
        continue

    try:
        ap = asb.XFoil(
            airfoil=af,
            Re=Re,
            n_crit=9
        ).alpha_sweep(alpha=alpha_range)
    except Exception as e:
        print(f"❌ XFoil failed for {name}: {e}")
        continue

    alphas = ap["alpha"]
    Cl = ap["CL"]
    Cd = ap["CD"]
    Cm = ap["CM"]
    Cpmin = ap.get("Cpmin", [np.nan] * len(alphas))  # not always available

    for i, alpha in enumerate(alphas):
        results.append({
            "airfoil": name,
            "Re": float(np.round(Re, 0)),
            "alpha": alpha,
            "Cl": Cl[i],
            "Cd": Cd[i],
            "Cm": Cm[i],
            "Cl/Cd": Cl[i] / Cd[i] if Cd[i] > 0 else np.nan,
            "Cl^(3/2)/Cd": (Cl[i] ** 1.5) / Cd[i] if Cd[i] > 0 else np.nan,
            "sqrt(Cl)": np.sqrt(Cl[i]) if Cl[i] > 0 else np.nan,
            "Cpmin": Cpmin[i],
            "Xtr_top": np.nan,   # not exposed by AeroSandbox XFoil
            "Xtr_bot": np.nan
        })


# === Save to CSV ===
df = pd.DataFrame(results)
df.to_csv("airfoil_polar_results.csv", index=False)

print("\n✅ Results saved to airfoil_polar_results.csv")
print(df.head())


# === Plot Example (Cl vs Alpha) ===
plt.figure(figsize=(8, 6))
for name in airfoil_list:
    subset = df[df["airfoil"] == name]
    if not subset.empty:
        plt.plot(subset["alpha"], subset["Cl"], label=name)

plt.xlabel("Angle of Attack (deg)")
plt.ylabel("Lift Coefficient (Cl)")
plt.title(f"Lift Curve at Re={Re:.0e}")
plt.legend()
plt.grid(True)
plt.savefig("Cl_vs_alpha.png", dpi=300)
plt.show()
