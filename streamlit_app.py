import streamlit as st
import numpy as np
import plotly as go

# ==========================================
# ⬅️ SIDEBAR CONTROL PANEL (LEFT COLUMN)
# ==========================================
with st.sidebar:
    st.header("🏹 Trajectory Settings")

    shooter_type = st.radio(
        "Shooter Mechanism Type",
        options=["Single Flywheel (with Hood)", "Dual Wheel Shooter"],
        index=0
    )
    
    efficiency_loss = st.slider('Efficiency Loss [%]', 0.0, 50.0, 10.0, 0.5) # e.g. 10% loss due to slip/compression

    angle = st.slider('Angle [deg]', 1.0, 90.0, 45.0, 0.5) 
    height_mm = st.slider('Height [mm]', 1.0, 450.0, 100.0, 0.1) 
    wheel_Radius_inch = st.slider('Wheel Radius [inch]', 0.5, 8.0, 2.0, 0.25) 
    velocity_RPM = st.slider('Speed [RPM]', 1000, 18000, 6000, 100) 


height_m = height_mm / 1000.0 
wheel_Radius_meter = wheel_Radius_inch * 0.0254

wheel_surface_speed = velocity_RPM * (2 * np.pi / 60) * wheel_Radius_meter

if shooter_type == "Single Flywheel (with Hood)":
    base_velocity_ms = wheel_surface_speed * 0.5  # Projectile rolls, cutting exit speed in half
else:
    base_velocity_ms = wheel_surface_speed        # Dual active wheels push at full surface speed

efficiency_multiplier = (100.0 - efficiency_loss) / 100.0
velocity_ms = base_velocity_ms * efficiency_multiplier

gravity = 9.81 
nmbr_pts = 100

def calculate_trajectory(u, angle_deg, h, g, points):
    # 1. Convert angle to radians and get velocity components
    theta = np.radians(angle_deg)
    ux = u * np.cos(theta)
    uy = u * np.sin(theta)
    
    # 2. Calculate exact total flight time using the quadratic formula
    discriminant = (uy ** 2) + (2 * g * h)
    t_flight = (uy + np.sqrt(discriminant)) / g
    total_range = ux * t_flight
    
    # 3. Generate horizontal distances (x) from start to impact
    x_positions = np.linspace(0, total_range, points)
    
    # 4. Trajectory equation: y = h + x*tan(theta) - (g*x^2) / (2 * u^2 * cos^2(theta))
    cos_theta = np.cos(theta)
    y_positions = h + x_positions * np.tan(theta) - (g * x_positions**2) / (2 * u**2 * cos_theta**2)
    
    # 5. Peak height milestone
    h_max = h + (uy**2) / (2 * g) if uy > 0 else h

    return {
        "calculated_velocity_ms": u,
        "flight_time_seconds": t_flight,
        "max_range_meters": total_range,
        "peak_height_meters": h_max,
        "x_coordinates": x_positions,
        "y_coordinates": y_positions,
    }

# --- Execute Calculations ---
results = calculate_trajectory(
    u=velocity_ms, 
    angle_deg=angle, 
    h=height_mm, 
    g=gravity, 
    points=nmbr_pts
)

# ==========================================
# 🔄 CONVERT OUTPUT BACK TO MILLIMETERS (m -> mm)
# ==========================================
max_range_mm = results['max_range_meters'] * 1000.0
peak_height_mm = results['peak_height_meters'] * 1000.0
x_coords_mm = results['x_coordinates'] * 1000.0
y_coords_mm = results['y_coordinates'] * 1000.0

# --- Streamlit Display ---
st.title("🏹 Shooter Angle & Speed Calculation")
st.markdown("Adjust parameters in the left sidebar configuration block to evaluate live path trends.")

st.write("### Trajectory Path")

# 🔄 ROUND THE COORDINATE ARRAYS TO 3 DECIMAL PLACES (1 mm precision)
rounded_x = np.round(results['x_coordinates'], 2)
rounded_y = np.round(results['y_coordinates'], 2)

# Format coordinates into a dictionary for st.line_chart
chart_data = {
    "Horizontal Distance (m)": rounded_x,
    "Vertical Height (m)": rounded_y
}

# Render the graph mapping X and Y axes explicitly
st.line_chart(
    data=chart_data,
    x="Horizontal Distance (m)",
    y="Vertical Height (m)"
)

fig = go.Figure()

# Layer 1: Plot the continuous ball trajectory line
fig.add_trace(go.Scatter(
    x=rounded_x, 
    y=rounded_y, 
    mode='lines',
    name='Trajectory Curve',
    line=dict(color='#0071e3', width=3)
))

# Layer 2: Plot the single Goal target node
fig.add_trace(go.Scatter(
    x=[target_x], 
    y=[target_y], 
    mode='markers',
    name='Goal / Target',
    marker=dict(color='#FF3B30', size=14, symbol='circle-x') # Distinct Red cross hair marker
))

# Configure Grid constraints and Axis Labels
fig.update_layout(
    xaxis_title="Horizontal Distance (m)",
    yaxis_title="Vertical Height (m)",
    hovermode="x unified",
    margin=dict(l=40, r=40, t=20, b=40),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    # Optional constraint: Locks x and y to 1:1 visually so angles aren't skewed
    yaxis=dict(scaleanchor="x", scaleratio=1, min_allowed=0)
)

# Render the custom Plotly chart object inside Streamlit 
st.plotly_chart(fig, use_container_width=True)