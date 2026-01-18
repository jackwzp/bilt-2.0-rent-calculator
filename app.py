
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(layout="wide")

st.title("Bilt 2.0 Rent Points Calculator")

# Input fields
monthly_rent = st.number_input("Monthly Rent ($)", min_value=0.0, value=2000.0, step=100.0)
estimated_non_rent = st.number_input("Estimated Monthly Non-Rent Payments ($)", min_value=0.0, value=500.0, step=50.0)



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

# Calculate points for user's input
points_method1 = calculate_method1_points(monthly_rent, estimated_non_rent)
points_method2 = calculate_method2_points(monthly_rent, estimated_non_rent)

st.subheader("Your Rent Points Earned:")
st.write(f"Option 1 (Tier Based): {points_method1:.2f} points")  # Corrected display text
st.write(f"Option 2 (Bilt Cash): {points_method2:.2f} points") # Corrected display text

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
        y=alt.Y('Option 1:Q', title='Points Earned')
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

    # Combine all layers
    chart = (vertical_line + user_markers + line1 + line2 + points1 + points2).properties(
        height=500
    ).configure_view(
        strokeWidth=0  # Remove border
    )

    st.altair_chart(chart, use_container_width=True)

    # st.markdown(f"Your current position: ${estimated_non_rent:.2f} non-rent spent, Option 1: {points_method1:.2f} points, Option 2: {points_method2:.2f} points")
else:
    st.write("Please enter a monthly rent greater than 0 to see the plots.")
