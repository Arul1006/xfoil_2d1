# 1. Import necessary libraries
import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt

# 2. Define the Aircraft Geometry
# We create an Airplane object with a single rectangular wing.

reynolds_list = [
    30000, 35553, 42123, 49911, 59139,
    70068, 83011, 98363, 116551, 138118,
    163651, 193910, 229792, 272266, 322648,
    382424, 453147, 536968, 636257, 753894,
    893197, 1058287, 1253844, 1485675, 1760334,
    2086034, 2472147, 2930262, 3472093, 4114740
]

asb.Airfoil()

naca2412_airfoil = asb.Airfoil("naca2412").generate_polars(
    reynolds_list,
    
)

airplane = asb.Airplane(
    name="Basic Test Aircraft",
    wings=[
        asb.Wing(
            name="Main Wing",
            xsecs=[
                asb.WingXSec( # Root cross-section (at the fuselage)
                    xyz_le=[0, 0, 0],       # Coordinates of the leading edge
                    chord=0.3,              # Chord length at this section
                    twist=0,                # Wing twist in degrees
                    airfoil=naca2412_airfoil # Airfoil shape
                ),
                asb.WingXSec( # Tip cross-section (at the wingtip)
                    xyz_le=[0, 1.5, 0],     # 1.5-meter half-span
                    chord=0.2,             # Tapered wing chord
                    twist=-2,               # Washout (negative twist) for stability
                    airfoil=naca2412_airfoil
                )
            ],
            symmetric=True, # Models the other half of the wing automatically
        ),
        asb.Wing(
            name="Tail Wing",
            xsecs=[
                asb.WingXSec( # Root
                    xyz_le=[0.8, 0, 0],
                    chord=0.2,
                    twist=0,
                    airfoil=naca2412_airfoil
                ),
                asb.WingXSec( # Tip
                    xyz_le=[0.8, 0.3, 0],
                    chord=0.2,
                    airfoil=naca2412_airfoil
                )
            ],
            symmetric=True
        ),
        asb.Wing(
            name = "Horizontal Stab",
            xsecs=[
                asb.WingXSec(
                    xyz_le=[0.8,0,0],
                    chord=0.2,
                    airfoil=naca2412_airfoil
                ),
                asb.WingXSec(
                    xyz_le=[0.8,0,0.3],
                    chord=0.2,
                    airfoil=naca2412_airfoil
                )
            ],
            symmetric=False
        ),
    ]
)

# 3. Define the Alpha Sweep Range and Flight Condition
# Define the range of angles of attack to analyze.
alpha_range = np.linspace(-15, 25, 80) # From -5 to 15 degrees in 21 steps.

# Define the atmospheric conditions (held constant for the sweep).
atmosphere = asb.Atmosphere(
    altitude=1000  # meters
)

# Initialize lists to store the results from each iteration.
CL_values = []
CD_values = []
Cm_values = []

print("Running analysis sweep over angles of attack...")

# 4. Loop Through Alphas and Run Analysis
for alpha in alpha_range:
    # Define the operating point for the current alpha.
    op_point = asb.OperatingPoint(
        velocity=40,
        alpha=alpha, # Use the current alpha from the loop
        atmosphere=atmosphere
    )

    # Set up and run the aerodynamic analysis.
    aero_problem = asb.VortexLatticeMethod(
        airplane=airplane,
        op_point=op_point,
    )
    results = aero_problem.run()

    # Store the results.
    CL_values.append(results['CL'])
    CD_values.append(results['CD'])
    Cm_values.append(results['Cm'])
    print(f"  Alpha: {alpha:5.1f} deg -> CL: {results['CL']:.4f}, CD: {results['CD']:.4f}, Cm: {results['Cm']:.4f}")

print("Sweep complete.")

# 5. Plot the Results
# Create a new figure for the plots.
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 12), sharex=True)
fig.suptitle("Aerodynamic Coefficients vs. Angle of Attack", fontsize=16)

# Plot CL vs. Alpha
ax1.plot(alpha_range, CL_values, 'o-')
ax1.set_ylabel("Lift Coefficient (CL)")
ax1.grid(True)

# Plot CD vs. Alpha
ax2.plot(alpha_range, CD_values, 'o-')
ax2.set_ylabel("Drag Coefficient (CD)")
ax2.grid(True)

# Plot Cm vs. Alpha
ax3.plot(alpha_range, Cm_values, 'o-')
ax3.set_xlabel("Angle of Attack [degrees]")
ax3.set_ylabel("Pitching Moment (Cm)")
ax3.grid(True)

# Display the plots.
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

# 6. Plot Aerodynamic Efficiency (L/D)
plt.figure(figsize=(8, 6))
lift_to_drag = np.array(CL_values) / np.array(CD_values)
plt.plot(alpha_range, lift_to_drag, 'o-')
plt.title("Aerodynamic Efficiency (L/D)")
plt.xlabel("Angle of Attack [degrees]")
plt.ylabel("Lift-to-Drag Ratio (L/D)")
plt.grid(True)
plt.show()

