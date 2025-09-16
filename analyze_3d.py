import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def analyze_3d():
    ### Example wing definition
    wing = asb.Wing(
        name="Main Wing",
        xsecs=[
            asb.WingXSec(  # root
                xyz_le=[0, 0, 0],
                chord=1.0,
                airfoil=asb.Airfoil("naca2412")
            ),
            asb.WingXSec(  # tip
                xyz_le=[2.0, 5.0, 0],
                chord=0.5,
                airfoil=asb.Airfoil("naca2412")
            ),
        ]
    )

    airplane = asb.Airplane(
        name="Test Plane",
        xyz_ref=[0, 0, 0],
        wings=[wing]
    )

    op_point = asb.OperatingPoint(
        velocity=30,
        alpha=5,
        beta=0,
        p=0, q=0, r=0
    )

    vlm = asb.VortexLatticeMethod(
        airplane=airplane,
        op_point=op_point,
    )

    sol = vlm.run()

    # --- Safer printing ---
    print("✅ 3D Analysis Results")
    print("Available keys:", list(sol.keys()))

    # Always print CL
    if "CL" in sol:
        print("CL:", sol["CL"])

    # Handle drag safely
    if "CDi" in sol:
        print("CDi (from solver):", sol["CDi"])
    else:
        try:
            CDi = vlm.induced_drag()
            print("CDi (computed):", CDi)
        except Exception:
            print("⚠️ Induced drag not available")

    if "CD" in sol:
        print("CD (total):", sol["CD"])

    if "Cm" in sol:
        print("Cm:", sol["Cm"])

    # Example plot (just to confirm wing planform)
    wing.draw(show=True)


if __name__ == "__main__":
    analyze_3d()
