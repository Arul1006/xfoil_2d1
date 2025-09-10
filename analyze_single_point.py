import subprocess
import pandas as pd
import os
import re


def analyze_single_point(filepath, airfoil_name, Re, alpha, mach):
    """
    Runs XFOIL for a single point and extracts detailed data like XCp and Cpmn.
    """
    print(f"🔹 Performing single-point analysis for {airfoil_name} at Re={Re}, alpha={alpha}...")

    xfoil_commands = f"""
LOAD {os.path.basename(filepath)}
PANE
OPER
VISC {Re}
MACH {mach}
ALFA {alpha}
QUIT
"""
    try:
        result = subprocess.run(
            ["xfoil.exe"],
            input=xfoil_commands,
            cwd=os.path.dirname(filepath),
            capture_output=True,
            text=True,
            timeout=30
        )
    except FileNotFoundError:
        print("❌ XFoil executable not found. Please ensure 'xfoil.exe' is in your system's PATH.")
        return None

    # Check for convergence and parse output
    if "VISC" not in result.stdout:
        print(f"❌ XFOIL failed to converge for {airfoil_name} at alpha={alpha}.")
        return None

    # Use regular expressions to find the required values
    cl_match = re.search(r'Cl\s*=\s*([-\d.]+)', result.stdout)
    cd_match = re.search(r'Cd\s*=\s*([-\d.]+)', result.stdout)
    cm_match = re.search(r'Cm\s*=\s*([-\d.]+)', result.stdout)
    xcp_match = re.search(r'Xcp\s*=\s*([-\d.]+)', result.stdout)
    cpmn_match = re.search(r'Cpmn\s*=\s*([-\d.]+)', result.stdout)

    data = {
        'airfoil': [airfoil_name],
        'Re': [Re],
        'alpha': [alpha],
        'CL': [float(cl_match.group(1)) if cl_match else None],
        'CD': [float(cd_match.group(1)) if cd_match else None],
        'CM': [float(cm_match.group(1)) if cm_match else None],
        'XCp': [float(xcp_match.group(1)) if xcp_match else None],
        'Cpmn': [float(cpmn_match.group(1)) if cpmn_match else None],
    }

    return pd.DataFrame(data)


def batch_analyze_single_points(airfoils: dict, params: dict):
    """
    Runs a single-point analysis for a set of airfoils and a few key conditions.
    """
    all_dfs = []

    # Define a few specific points for detailed analysis
    analysis_points = [
        {"alpha": 5, "Re": 1e6},
        {"alpha": 10, "Re": 3e6}
    ]

    for point in analysis_points:
        for af_name, af_path in airfoils.items():
            df = analyze_single_point(
                af_path,
                af_name,
                point["Re"],
                point["alpha"],
                params["mach"]
            )
            if df is not None:
                all_dfs.append(df)

    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        full_df.to_csv("single_point_analysis.csv", index=False)
        print("✅ Saved single-point results to single_point_analysis.csv")
    else:
        print("⚠️ No single-point results generated.")