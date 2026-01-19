import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(
    layout="wide",
    page_title="Bilt 2.0 Rent Pts Calculator",
    page_icon="🚀"
)

st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("Bilt 2.0 Rent Points Calculator")

st.info(
    body="[Watch video breakdown](https://youtu.be/yrPa71fNy2k) of this tool. This calculator compares the Bilt 2.0 rent points earned from the [two different rent options](https://newsroom.biltrewards.com/biltcardupdate).",
    icon="ℹ️"
)

# Input fields
st.subheader("Enter your rent and non-rent estimates:")
monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, value=2000.0, step=100.0)
estimated_non_rent = st.number_input("Estimated Monthly Non-Rent Payments Using Bilt Card ($)", min_value=0.0, value=500.0, step=50.0)

# Intersection point color picker
intersection_color ="#804509"

# Calculation Option 2: Linear Function
def calculate_method2_points(rent, non_rent):
    points = non_rent * 0.04 * 100 / 3
    return min(points, rent)

# Calculation Option 1: Step Function
def calculate_method1_points(rent, non_rent):
    non_rent_percentage = (non_rent / rent) * 100 if rent > 0 else 0
    if non_rent_percentage >= 100:
        multiplier = 1.25
    elif non_rent_percentage >= 75:
        multiplier = 1.0
    elif non_rent_percentage >= 50:
        multiplier = 0.75
    elif non_rent_percentage >= 25:
        multiplier = 0.5
    else:
        return 250 # Earn 250 points with 0 spend
    return multiplier * rent

# Function to find intersection points
def find_intersections(rent_val):
    """Find where Option 1 and Option 2 earn equal points"""
    intersections = []

    # Check various non-rent spend values
    non_rent_values = np.linspace(0, rent_val * 1.5, 10000)

    prev_diff = None
    prev_equal = False
    in_equal_segment = False

    for i, non_rent in enumerate(non_rent_values):
        m1 = calculate_method1_points(rent_val, non_rent)
        m2 = calculate_method2_points(rent_val, non_rent)
        diff = abs(m1 - m2)

        # Check if values are equal (within small tolerance)
        is_equal = diff < 0.01

        # Detect start of equal segment (lines meet or overlap)
        if is_equal and not in_equal_segment:
            # Mark the first point where they become equal
            # Snap to exact percentage thresholds if close
            intersection_point = non_rent
            for pct in [0.25, 0.5, 0.75, 1.0]:
                threshold = pct * rent_val
                if abs(non_rent - threshold) < rent_val * 0.01:
                    intersection_point = threshold
                    break

            intersections.append({
                'non_rent': intersection_point,
                'points': calculate_method1_points(rent_val, intersection_point)
            })
            in_equal_segment = True

        # Detect end of equal segment (lines diverge)
        if not is_equal and in_equal_segment:
            in_equal_segment = False

        # Detect crossing (sign change when not in equal segment)
        if prev_diff is not None and not in_equal_segment and not prev_equal:
            sign_change = (m1 - m2) * (prev_diff) < 0
            if sign_change:
                # Refine the intersection point
                left = non_rent_values[i-1]
                right = non_rent

                # Binary search for precise intersection
                for _ in range(50):
                    mid = (left + right) / 2
                    m1_mid = calculate_method1_points(rent_val, mid)
                    m2_mid = calculate_method2_points(rent_val, mid)
                    diff_mid = m1_mid - m2_mid

                    if abs(diff_mid) < 0.01:
                        # Snap to exact percentage thresholds if close
                        intersection_point = mid
                        for pct in [0.25, 0.5, 0.75, 1.0]:
                            threshold = pct * rent_val
                            if abs(mid - threshold) < rent_val * 0.005:
                                intersection_point = threshold
                                break

                        intersections.append({
                            'non_rent': intersection_point,
                            'points': calculate_method1_points(rent_val, intersection_point)
                        })
                        break

                    if np.sign(diff_mid) == np.sign(m1 - m2):
                        right = mid
                    else:
                        left = mid

        prev_diff = m1 - m2
        prev_equal = is_equal

    # Remove duplicates that are very close to each other
    filtered_intersections = []
    for inter in intersections:
        is_duplicate = False
        for existing in filtered_intersections:
            if abs(inter['non_rent'] - existing['non_rent']) < rent_val * 0.01:
                is_duplicate = True
                break
        if not is_duplicate:
            filtered_intersections.append(inter)

    return filtered_intersections

# Calculate points for user's input
points_method1 = calculate_method1_points(monthly_rent, estimated_non_rent)
points_method2 = calculate_method2_points(monthly_rent, estimated_non_rent)

st.subheader("Your Rent Points Earned:")
st.write(f"Option 1 (Tier Based): {points_method1:.2f} points")
st.write(f"Option 2 (Bilt Cash): {points_method2:.2f} points")

# Determine the better method
if points_method1 > points_method2:
    st.markdown(f"**Option 1 is better for you, earning {points_method1 - points_method2:.2f} more points!**")
elif points_method2 > points_method1:
    st.markdown(f"**Option 2 is better for you, earning {points_method2 - points_method1:.2f} more points!**")
else:
    st.markdown("**Both methods earn you the same number of points!**")

st.subheader("Rent Points Earned by Non-Rent Spent")

# Data for plotting
def generate_plot_data(rent_val):
    # Create base uniform distribution
    base_points = np.linspace(0, rent_val * 1.5, 500)

    # Add extra points near critical percentages
    critical_points = []
    for pct in [0.25, 0.5, 0.75, 1.0]:
        # Very dense points around each critical percentage
        critical_points.extend(
            np.linspace(pct * rent_val - 0.05 * rent_val,
                       pct * rent_val + 0.05 * rent_val,
                       100)
        )

    # Combine and remove duplicates
    non_rent_spents = np.unique(np.concatenate([base_points, critical_points]))
    non_rent_spents = non_rent_spents[(non_rent_spents >= 0) & (non_rent_spents <= rent_val * 1.5)]

    data = []
    for non_rent_spent in non_rent_spents:
        points_m1 = calculate_method1_points(rent_val, non_rent_spent)
        points_m2 = calculate_method2_points(rent_val, non_rent_spent)
        data.append({
            'Non-Rent Spent ($)': non_rent_spent,
            'Option 1': points_m1,
            'Option 2': points_m2,
        })
    return pd.DataFrame(data)

plot_df = generate_plot_data(monthly_rent)

if monthly_rent > 0:
    # Find intersection points
    intersections = find_intersections(monthly_rent)

    # Reshape data for proper tooltips on both lines
    plot_df_with_both = plot_df.copy()

    # Create a selection that chooses the nearest point based on x-value
    nearest = alt.selection_point(nearest=True, on='mouseover',
                                    fields=['Non-Rent Spent ($)'], empty=False)

    # Create base chart
    base = alt.Chart(plot_df_with_both).encode(
        x=alt.X('Non-Rent Spent ($):Q', title='Non-Rent Spent ($)', scale=alt.Scale(domain=[0, monthly_rent * 1.5]))
    )

    # Option 1 line only (no points)
    line1 = base.mark_line(color='#1f77b4', strokeWidth=2).encode(
        y=alt.Y('Option 1:Q', title='Rent Points Earned')
    )

    # Option 2 line only (no points)
    line2 = base.mark_line(color='#ff7f0e', strokeWidth=2).encode(
        y=alt.Y('Option 2:Q')
    )

    # Hover points for Option 1
    points1 = base.mark_point(color='#1f77b4', size=100, filled=True).encode(
        y='Option 1:Q',
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Non-Rent Spent'),
            alt.Tooltip('Option 1:Q', format='.2f', title='Option 1 Points'),
            alt.Tooltip('Option 2:Q', format='.2f', title='Option 2 Points')
        ]
    ).add_params(nearest)

    # Hover points for Option 2
    points2 = base.mark_point(color='#ff7f0e', size=100, filled=True).encode(
        y='Option 2:Q',
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Non-Rent Spent'),
            alt.Tooltip('Option 1:Q', format='.2f', title='Option 1 Points'),
            alt.Tooltip('Option 2:Q', format='.2f', title='Option 2 Points')
        ]
    )

    # User's current position markers
    user_position_df = pd.DataFrame({
        'Non-Rent Spent ($)': [estimated_non_rent, estimated_non_rent],
        'Points': [points_method1, points_method2],
        'Option': ['Option 1', 'Option 2']
    })

    user_markers = alt.Chart(user_position_df).mark_point(
        size=200,
        filled=True,
        shape='diamond',
        opacity=1
    ).encode(
        x='Non-Rent Spent ($):Q',
        y=alt.Y('Points:Q'),
        color=alt.Color('Option:N', scale=alt.Scale(domain=['Option 1', 'Option 2'], range=['#1f77b4', '#ff7f0e']))
    )

    # Vertical line at user's position
    vertical_line_df = pd.DataFrame({
        'x': [estimated_non_rent]
    })

    vertical_line = alt.Chart(vertical_line_df).mark_rule(
        color='gray',
        strokeDash=[5, 5],
        strokeWidth=2,
        opacity=0.7
    ).encode(
        x='x:Q'
    )

    # Add intersection markers
    intersection_layers = []
    if intersections:
        intersection_df = pd.DataFrame([
            {
                'Non-Rent Spent ($)': inter['non_rent'],
                'Points': inter['points']
            }
            for inter in intersections
        ])

        # Intersection point markers
        intersection_markers = alt.Chart(intersection_df).mark_point(
            size=300,
            filled=True,
            shape='circle',
            color=intersection_color,
            opacity=1,
            stroke='white',
            strokeWidth=2
        ).encode(
            x='Non-Rent Spent ($):Q',
            y='Points:Q',
            tooltip=[
                alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Intersection at'),
                alt.Tooltip('Points:Q', format='.2f', title='Points Earned')
            ]
        )

        # Text labels for x-axis values at intersections
        intersection_text = alt.Chart(intersection_df).mark_text(
            align='center',
            baseline='bottom',
            dy=-15,
            fontSize=12,
            fontWeight='bold',
            color=intersection_color
        ).encode(
            x='Non-Rent Spent ($):Q',
            y='Points:Q',
            text=alt.Text('Non-Rent Spent ($):Q', format='$,.2f')
        )

        intersection_layers = [intersection_markers, intersection_text]

    # Combine all layers
    chart = (vertical_line + user_markers + line1 + line2 + points1 + points2 +
             sum(intersection_layers, alt.LayerChart()) if intersection_layers else
             vertical_line + user_markers + line1 + line2 + points1 + points2).properties(
        height=500
    ).configure_view(
        strokeWidth=0  # Remove border
    )

    st.altair_chart(chart, use_container_width=True)

    # Display intersection information
    if intersections:
        st.subheader("Breakeven Points:")
        for i, inter in enumerate(intersections, 1):
            st.write(f"**Point {i}:** Both options earn **{inter['points']:.2f} points** when non-rent spending is **${inter['non_rent']:.2f}**")
else:
    st.write("Please enter a monthly rent greater than 0 to see the plots.")