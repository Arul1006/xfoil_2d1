# 1. Import AeroSandbox
import aerosandbox as asb
import aerosandbox.numpy as np

# 2. Define the Aircraft Geometry
airplane = asb.Airplane(
    name="Simple Analysis Wing",
    wings=[
        asb.Wing(
            name="Main Wing",
            xsecs=[
                asb.WingXSec( # Root
                    xyz_le=[0, 0, 0],
                    chord=0.3,
                    twist=0,
                    airfoil=asb.Airfoil("naca2412")
                ),
                asb.WingXSec( # Tip
                    xyz_le=[0, 1.0, 0],
                    chord=0.3,
                    twist=-2, # A fixed -2 degree twist
                    airfoil=asb.Airfoil("naca2412")
                )
            ],
            symmetric=True
        ),
        asb.Wing(
            name="Tail Wing",
            xsecs=[
                asb.WingXSec( # Root
                    xyz_le=[0.8, 0, 0],
                    chord=0.2,
                    twist=0,
                    airfoil=asb.Airfoil("naca2412")
                ),
                asb.WingXSec( # Tip
                    xyz_le=[0, 1.0, 0],
                    chord=0.2,
                    airfoil=asb.Airfoil("naca2412")
                )
            ],
            symmetric=True
        )
    ]
)

# 3. Define the Flight Condition (Operating Point)
# The CORRECT way:
atmosphere = asb.Atmosphere(
    altitude=0  # Sea level
)
op_point = asb.OperatingPoint(
    velocity=30,  # m/s
    alpha=5,      # 5 degrees angle of attack
    atmosphere=atmosphere
)

# 4. Set up and Run the Analysis
aero_problem = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=op_point,
)

results = aero_problem.run()

# 5. Print the Results
print("--- Static Analysis Complete ---")
print(f"Lift Coefficient (CL):   {results['CL']:.4f}")
print(f"Drag Coefficient (CD):   {results['CD']:.4f}")
print(f"Pitching Moment (Cm):    {results['Cm']:.4f}")
print(f"\nLift-to-Drag Ratio (L/D): {results['CL'] / results['CD']:.2f} 🚀")
#print(f"Stability Derivative (Cm_alpha): {results['Cm_alpha']:.4f}")

# Visualize the aircraft and forces
aero_problem.draw()