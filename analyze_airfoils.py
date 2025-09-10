import subprocess
import pandas as pd
import os
import re
import numpy as np
from datetime import datetime


def run_xfoil_and_parse_output(xfoil_commands: str, cwd: str, airfoil_name: str, Re: float, alpha: float):
    """
    Executes a single XFOIL process and parses the output for a specific point.
    Returns a dictionary of metrics.
    """
    print(f"🔹 Analyzing {airfoil_name} at Re={Re}, alpha={alpha}...")
    print('testing git')
    try:
        result = subprocess.run(
            ["xfoil.exe"],
            input=xfoil_commands,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
    except FileNotFoundError:
        print("❌ XFoil executable not found. Please ensure 'xfoil.exe' is in your system's PATH.")
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ XFoil process timed out for {airfoil_name} at Re={Re}, alpha={alpha}.")
        return None

    # Check for convergence and parse output
    if "VISC" not in result.stdout and "CL" not in result.stdout:
        print(f"❌ XFOIL failed to converge for {airfoil_name} at Re={Re}, alpha={alpha}.")
        return None

    # Use regular expressions to find all required values
    cl_match = re.search(r'Cl\s*=\s*([-\d.]+)', result.stdout)
    cd_match = re.search(r'Cd\s*=\s*([-\d.]+)', result.stdout)
    cm_match = re.search(r'Cm\s*=\s*([-\d.]+)', result.stdout)
    xcp_match = re.search(r'Xcp\s*=\s*([-\d.]+)', result.stdout)
    cpmn_match = re.search(r'Cpmn\s*=\s*([-\d.]+)', result.stdout)
    xtr_top_match = re.search(r'Side 1\s+(?:free\s+transition at|forced transition at)\s+x/c\s*=\s*([-\d.]+)',
                              result.stdout)
    xtr_bottom_match = re.search(r'Side 2\s+(?:free\s+transition at|forced transition at)\s+x/c\s*=\s*([-\d.]+)',
                                 result.stdout)

    data = {
        'alpha': float(alpha),
        'CL': float(cl_match.group(1)) if cl_match else np.nan,
        'CD': float(cd_match.group(1)) if cd_match else np.nan,
        'CM': float(cm_match.group(1)) if cm_match else np.nan,
        'XCp': float(xcp_match.group(1)) if xcp_match else np.nan,
        'Cpmn': float(cpmn_match.group(1)) if cpmn_match else np.nan,
        'Xtr_top': float(xtr_top_match.group(1)) if xtr_top_match else np.nan,
        'Xtr_bottom': float(xtr_bottom_match.group(1)) if xtr_bottom_match else np.nan
    }
    return data


def analyze_airfoils(airfoils: dict, params: dict):
    """
    Performs a batch analysis for a list of airfoils across multiple Reynolds numbers
    and returns a single DataFrame.
    """
    all_data = []

    for airfoil_name, airfoil_path in airfoils.items():
        for reynolds in params['reynolds']:
            for alpha in params['alphas']:
                xfoil_commands = f"""
LOAD {os.path.basename(airfoil_path)}
PANE
OPER
VISC {reynolds}
MACH {params['mach']}
ALFA {alpha}
QUIT
"""
                metrics = run_xfoil_and_parse_output(xfoil_commands, os.path.dirname(airfoil_path), airfoil_name,
                                                     reynolds, alpha)

                if metrics:
                    metrics['airfoil'] = airfoil_name
                    metrics['Re'] = reynolds
                    metrics['mach'] = params['mach']
                    all_data.append(metrics)

    if all_data:
        full_df = pd.DataFrame(all_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"combined_airfoil_data_{timestamp}.csv"
        full_df.to_csv(output_filename, index=False)
        print(f"✅ Saved all combined data to {output_filename}")
    else:
        print("❌ No data could be generated.")


# import subprocess
# import pandas as pd
# import os
# import re
# import numpy as np
# from datetime import datetime
#
#
# # Step 1: Add 'mach' to the function's parameters
# def run_xfoil_and_parse_output(xfoil_commands: str, cwd: str, airfoil_name: str, Re: float, alpha: float, mach: float):
#     """
#     Executes a single XFOIL process and parses the output for a specific point.
#     Returns a dictionary of metrics.
#     """
#     print(f"🔹 Analyzing {airfoil_name} at Re={Re}, alpha={alpha}...")
#     try:
#         result = subprocess.run(
#             ["xfoil.exe"],
#             input=xfoil_commands,
#             cwd=cwd,
#             capture_output=True,
#             text=True,
#             timeout=30
#         )
#     except FileNotFoundError:
#         print("❌ XFoil executable not found. Please ensure 'xfoil.exe' is in your system's PATH.")
#         return None
#     except subprocess.TimeoutExpired:
#         print(f"❌ XFoil process timed out for {airfoil_name} at Re={Re}, alpha={alpha}.")
#         return None
#
#     if "VISC" not in result.stdout and "CL" not in result.stdout:
#         print(f"❌ XFOIL failed to converge for {airfoil_name} at Re={Re}, alpha={alpha}.")
#         return None
#
#     cl_match = re.search(r'Cl\s*=\s*([-\d.]+)', result.stdout)
#     cd_match = re.search(r'Cd\s*=\s*([-\d.]+)', result.stdout)
#     cm_match = re.search(r'Cm\s*=\s*([-\d.]+)', result.stdout)
#     xcp_match = re.search(r'Xcp\s*=\s*([-\d.]+)', result.stdout)
#     cpmn_match = re.search(r'Cpmn\s*=\s*([-\d.]+)', result.stdout)
#     xtr_top_match = re.search(r'Side 1\s+(?:free\s+transition at|forced transition at)\s+x/c\s*=\s*([-\d.]+)',
#                               result.stdout)
#     xtr_bottom_match = re.search(r'Side 2\s+(?:free\s+transition at|forced transition at)\s+x/c\s*=\s*([-\d.]+)',
#                                  result.stdout)
#
#     data = {
#         'airfoil': airfoil_name,
#         'alpha': float(alpha),
#         'CL': float(cl_match.group(1)) if cl_match else np.nan,
#         'CD': float(cd_match.group(1)) if cd_match else np.nan,
#         'CM': float(cm_match.group(1)) if cm_match else np.nan,
#         'XCp': float(xcp_match.group(1)) if xcp_match else np.nan,
#         'Cpmn': float(cpmn_match.group(1)) if cpmn_match else np.nan,
#         'Xtr_top': float(xtr_top_match.group(1)) if xtr_top_match else np.nan,
#         'Xtr_bottom': float(xtr_bottom_match.group(1)) if xtr_bottom_match else np.nan,
#         'Re': Re,
#         'mach': mach
#     }
#     return data
#
#
# def analyze_airfoils(airfoils: dict, params: dict):
#     """
#     Performs a batch analysis for a list of airfoils across multiple Reynolds numbers
#     and returns a single DataFrame.
#     """
#     all_data = []
#
#     for airfoil_name, airfoil_path in airfoils.items():
#         for reynolds in params['reynolds']:
#             for alpha in params['alphas']:
#                 xfoil_commands = f"""
# LOAD {os.path.basename(airfoil_path)}
# PANE
# OPER
# VISC {reynolds}
# MACH {params['mach']}
# ALFA {alpha}
# QUIT
# """
#                 # Step 2: Pass the 'mach' value when calling the function
#                 metrics = run_xfoil_and_parse_output(xfoil_commands, os.path.dirname(airfoil_path), airfoil_name,
#                                                      reynolds, alpha, params['mach'])
#                 if metrics:
#                     all_data.append(metrics)
#
#     if all_data:
#         column_order = ['airfoil', 'Re', 'mach', 'alpha', 'CL', 'CD', 'CM', 'XCp', 'Cpmn', 'Xtr_top', 'Xtr_bottom']
#         full_df = pd.DataFrame(all_data, columns=column_order)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         output_filename = f"combined_airfoil_data_{timestamp}.csv"
#         full_df.to_csv(output_filename, index=False)
#         print(f"✅ Saved all combined data to {output_filename}")
#     else:
#         print("❌ No data could be generated.")