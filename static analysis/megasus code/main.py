import aerosandbox as asb
import aerosandbox.numpy as np
import math # Allows use of math functions like sqrt() in config strings

# ##############################################################################
# # --- CONFIGURATION ---
# # All of your inputs go in this section.
# ##############################################################################

config = {
    # === Mission and Flight Conditions ===
    "mission": {
        "velocity"    : 30,  # meters per second
        "altitude"    : 1000, # meters
        "payload_mass": 2,    # kilograms
    },

    # === Design Variables ===
    # List of all parameters the optimizer is allowed to change.
    # The 'name' is a string used to link to the geometry below.
    "variables": {
        "aspect_ratio": {"init_guess": 10, "lower_bound": 6,  "upper_bound": 15},
        "wing_area"   : {"init_guess": 1.25, "lower_bound": 0.5, "upper_bound": 3.0},
        "cruise_alpha": {"init_guess": 5, "lower_bound": 0, "upper_bound": 10},
        "h_stab_area" : {"init_guess": 0.2, "lower_bound": 0.1, "upper_bound": 0.5},
        "v_stab_area" : {"init_guess": 0.15, "lower_bound": 0.1, "upper_bound": 0.4},
    },

    # === Aircraft Components ===
    # Define the physical parts of the airplane.
    # Geometry values are STRINGS that can be numbers, variable names, or formulas.
    "components": {
        "wing": {
            "geometry": {
                "span"   : "np.sqrt(aspect_ratio * wing_area)",
                "chord"  : "wing_area / np.sqrt(aspect_ratio * wing_area)",
                "airfoil": "naca2412",
            },
            "material": {
                "type" : "areal_density",  # kg/m^2
                "value": 1.5
            }
        },
        "h_stab": {
            "geometry": {
                "span"   : "np.sqrt(8 * h_stab_area)", # Assume AR=8 for tail
                "chord"  : "h_stab_area / np.sqrt(8 * h_stab_area)",
                "airfoil": "naca0012",
            },
            "xyz_le": [3.0, 0, 0], # Position of the horizontal tail
            "material": {
                "type" : "areal_density",
                "value": 1.2
            }
        },
        "v_stab": {
            "geometry": {
                "span"   : "np.sqrt(4 * v_stab_area)", # Assume AR=4 for tail
                "chord"  : "v_stab_area / np.sqrt(4 * v_stab_area)",
                "airfoil": "naca0012",
            },
            "xyz_le": [3.0, 0, 0], # Position of the vertical tail
            "material": {
                "type" : "areal_density",
                "value": 1.2
            }
        },
        "fuselage": {
            "geometry": {
                "length": 3.5,
                "radius": 0.15,
            },
            "material": {
                "type" : "density", # kg/m^3
                "value": 25
            }
        }
    },

    # === Optimization Goal ===
    # Choose one: "Maximize L/D", "Minimize Drag", "Minimize Mass"
    "goal": {
        "objective": "Maximize L/D"
    },

    # === Constraints ===
    # Add any additional rules for the design.
    "constraints": {
        "stall_avoidance": {
            "max_alpha_deg": 12
        },
        # "max_weight": {
        #     "value_kg": 20
        # }
    }
}

# ##############################################################################
# # --- OPTIMIZATION ENGINE ---
# # The code below translates your configuration into a solvable problem.
# # You shouldn't need to edit anything here.
# ##############################################################################

# --- Setup ---
opti = asb.Opti()
vars = {} # This dictionary will hold the symbolic optimization variables

# --- Create Symbolic Variables ---
for name, properties in config["variables"].items():
    vars[name] = opti.variable(
        init_guess=properties["init_guess"],
        lower_bound=properties.get("lower_bound"), # .get() handles optional bounds
        upper_bound=properties.get("upper_bound"),
    )

# --- Build Aircraft Components Symbolically ---
wings = []
fuselages = []


def eval_expr(expr_str):
    """
    Safely evaluates a geometry expression string in the context of our variables.
    The context includes all defined variables and the 'math' module.
    """
    return eval(expr_str, {"np": np}, vars)

# Build Wings and Tails
for name, comp in config["components"].items():
    if name in ["wing", "h_stab", "v_stab"]:
        wings.append(
            asb.Wing(
                name=name,
                symmetric=True if name != "v_stab" else False,
                xsecs=[
                    asb.WingXSec(
                        chord=eval_expr(str(comp["geometry"]["chord"])),
                        airfoil=asb.Airfoil(name=comp["geometry"]["airfoil"])
                    )
                ],
                span=eval_expr(str(comp["geometry"]["span"])),
                xyz_le=comp.get("xyz_le", [0, 0, 0]),
                material=asb.library.material.Material(**{comp["material"]["type"]: comp["material"]["value"]})
            )
        )

# Build Fuselages
for name, comp in config["components"].items():
    if name == "fuselage":
        fuselages.append(
            asb.Fuselage(
                name=name,
                xsecs=[
                    asb.FuselageXSec(xyz_c=[0, 0, 0], radius=comp["geometry"]["radius"]),
                    asb.FuselageXSec(xyz_c=[comp["geometry"]["length"], 0, 0], radius=comp["geometry"]["radius"])
                ],
                material=asb.library.material.Material(**{comp["material"]["type"]: comp["material"]["value"]})
            )
        )

airplane = asb.Airplane(wings=wings, fuselages=fuselages)
airplane.set_ref_dims_from_wing()

# --- Physics Analysis ---
# Mass Properties
mass_props = airplane.mass_properties()
total_mass = mass_props["mass"] + config["mission"]["payload_mass"]

# Aerodynamics
op_point = asb.OperatingPoint(
    velocity=config["mission"]["velocity"],
    altitude=config["mission"]["altitude"],
    alpha=vars["cruise_alpha"] if "cruise_alpha" in vars else 0
)
aero = asb.AeroBuildup(airplane=airplane, op_point=op_point).run()

# --- Define Objective ---
lift_to_drag_ratio = aero['CL'] / aero['CD']

if config["goal"]["objective"] == "Maximize L/D":
    opti.minimize(-lift_to_drag_ratio)
elif config["goal"]["objective"] == "Minimize Drag":
    opti.minimize(aero['CD'])
elif config["goal"]["objective"] == "Minimize Mass":
    opti.minimize(total_mass)

# --- Define Constraints ---
# Lift must equal weight
lift_force = aero['CL'] * op_point.dynamic_pressure() * airplane.s_ref
weight_force = total_mass * 9.81
opti.subject_to(lift_force == weight_force)

# Add constraints from config
if "stall_avoidance" in config["constraints"]:
    opti.subject_to(
        vars["cruise_alpha"] < config["constraints"]["stall_avoidance"]["max_alpha_deg"]
    )
if "max_weight" in config["constraints"]:
    opti.subject_to(
        total_mass < config["constraints"]["max_weight"]["value_kg"]
    )

# --- Solve and Report ---
sol = opti.solve()

print("\n" + "="*50)
print("OPTIMIZATION COMPLETE")
print("="*50)
print(f"Objective: {config['goal']['objective']}")
print("\n--- Optimal Design Variables ---")
for name, var in vars.items():
    print(f"{name:<20}: {sol.value(var):.3f}")

print("\n--- Performance Metrics ---")
print(f"{'Total Mass (with payload)':<25}: {sol.value(total_mass):.3f} kg")
print(f"{'Lift/Drag Ratio':<25}: {sol.value(lift_to_drag_ratio):.3f}")
print(f"{'CL':<25}: {sol.value(aero['CL']):.3f}")
print(f"{'CD':<25}: {sol.value(aero['CD']):.4f}")
print("="*50)