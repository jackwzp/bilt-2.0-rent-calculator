import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import COLORS, DEFAULT_RENT, DEFAULT_NON_RENT
from utils.calculations import calculate_method1_points, calculate_method2_points, find_intersections
from utils.charts import get_brand_css

st.set_page_config(
    layout="wide",
    page_title="Rent Options | Bilt Calculator",
    page_icon=":material/calculate:",
)

# Apply brand CSS
st.markdown(get_brand_css(), unsafe_allow_html=True)

st.title("Rent Options Calculator")

# Link to full comparison

st.info(body="""
**Want to compare all Bilt cards?** This rent options calculator applies to all Bilt 2.0 cards equally.
To see which card gives you the best overall value (including non-rent points, sign-up bonuses, and credits),
check out the **Card Comparison** page in the sidebar.
""")

st.markdown("""
[Watch video breakdown](https://youtu.be/d1EZCjpGsIk) of this calculator.
It compares the [two different rent options](https://newsroom.biltrewards.com/biltcardupdate) you can choose during onboarding.

**Option 1 (Tier-based):** Earn up to 1.25X your rent in points based on your non-rent spending tier.

**Option 2 (Bilt Cash):** Earn rent points at $3 Bilt Cash for 100 points, capped at your rent amount.
""")

st.divider()


# Input fields
st.subheader("Enter your rent and non-rent estimates:")
col1, col2 = st.columns(2)

with col1:
    monthly_rent = st.number_input(
        "Monthly Rent/Mortgage ($)",
        min_value=0.0,
        value=DEFAULT_RENT,
        step=100.0,
    )

with col2:
    estimated_non_rent = st.number_input(
        "Estimated Monthly Non-Rent Payments ($)",
        min_value=0.0,
        value=500.0,
        step=50.0,
    )

# Colors from brand
option1_color = COLORS['teal']
option2_color = COLORS['orange']
intersection_color = COLORS['amber']

# Calculate points for user's input
points_method1 = calculate_method1_points(monthly_rent, estimated_non_rent)
points_method2 = calculate_method2_points(monthly_rent, estimated_non_rent)

st.subheader("Your Rent Points Earned:")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Option 1 (Tier Based)",
        value=f"{points_method1:,.0f} points",
    )

with col2:
    st.metric(
        label="Option 2 (Bilt Cash)",
        value=f"{points_method2:,.0f} points",
    )

# Determine the better method
diff = abs(points_method1 - points_method2)
if points_method1 > points_method2:
    st.success(f"**Option 1 is better for you**, earning {diff:,.0f} more points!")
elif points_method2 > points_method1:
    st.success(f"**Option 2 is better for you**, earning {diff:,.0f} more points!")
else:
    st.info("**Both options earn you the same number of points!**")

st.subheader("Rent Points Earned by Non-Rent Spent")


# Data for plotting
def generate_plot_data(rent_val):
    base_points = np.linspace(0, rent_val * 1.5, 500)

    critical_points = []
    for pct in [0.25, 0.5, 0.75, 1.0]:
        critical_points.extend(
            np.linspace(pct * rent_val - 0.05 * rent_val,
                       pct * rent_val + 0.05 * rent_val,
                       100)
        )

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


if monthly_rent > 0:
    plot_df = generate_plot_data(monthly_rent)
    intersections = find_intersections(monthly_rent)

    plot_df_with_both = plot_df.copy()

    nearest = alt.selection_point(nearest=True, on='mouseover',
                                    fields=['Non-Rent Spent ($)'], empty=False)

    base = alt.Chart(plot_df_with_both).encode(
        x=alt.X('Non-Rent Spent ($):Q',
                title='Non-Rent Spent ($)',
                scale=alt.Scale(domain=[0, monthly_rent * 1.5]),
                axis=alt.Axis(format='$,.0f'))
    )

    line1 = base.mark_line(color=option1_color, strokeWidth=3).encode(
        y=alt.Y('Option 1:Q', title='Rent Points Earned')
    )

    line2 = base.mark_line(color=option2_color, strokeWidth=3).encode(
        y=alt.Y('Option 2:Q')
    )

    points1 = base.mark_point(color=option1_color, size=100, filled=True).encode(
        y='Option 1:Q',
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Non-Rent Spent'),
            alt.Tooltip('Option 1:Q', format='.0f', title='Option 1 Points'),
            alt.Tooltip('Option 2:Q', format='.0f', title='Option 2 Points')
        ]
    ).add_params(nearest)

    points2 = base.mark_point(color=option2_color, size=100, filled=True).encode(
        y='Option 2:Q',
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Non-Rent Spent'),
            alt.Tooltip('Option 1:Q', format='.0f', title='Option 1 Points'),
            alt.Tooltip('Option 2:Q', format='.0f', title='Option 2 Points')
        ]
    )

    user_position_df = pd.DataFrame({
        'Non-Rent Spent ($)': [estimated_non_rent, estimated_non_rent],
        'Points': [points_method1, points_method2],
        'Option': ['Option 1', 'Option 2']
    })

    user_markers = alt.Chart(user_position_df).mark_point(
        size=250,
        filled=True,
        shape='diamond',
        opacity=1
    ).encode(
        x='Non-Rent Spent ($):Q',
        y=alt.Y('Points:Q'),
        color=alt.Color('Option:N',
                       scale=alt.Scale(
                           domain=['Option 1', 'Option 2'],
                           range=[option1_color, option2_color]
                       ))
    )

    vertical_line_df = pd.DataFrame({
        'x': [estimated_non_rent]
    })

    vertical_line = alt.Chart(vertical_line_df).mark_rule(
        color=COLORS['gray'],
        strokeDash=[5, 5],
        strokeWidth=2,
        opacity=0.7
    ).encode(
        x='x:Q'
    )

    intersection_layers = []
    if intersections:
        intersection_df = pd.DataFrame([
            {
                'Non-Rent Spent ($)': inter['non_rent'],
                'Points': inter['points']
            }
            for inter in intersections
        ])

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
                alt.Tooltip('Non-Rent Spent ($):Q', format='$,.2f', title='Breakeven at'),
                alt.Tooltip('Points:Q', format='.0f', title='Points Earned')
            ]
        )

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
            text=alt.Text('Non-Rent Spent ($):Q', format='$,.0f')
        )

        intersection_layers = [intersection_markers, intersection_text]

    if intersection_layers:
        chart = (vertical_line + user_markers + line1 + line2 + points1 + points2 +
                 intersection_layers[0] + intersection_layers[1])
    else:
        chart = vertical_line + user_markers + line1 + line2 + points1 + points2

    chart = chart.properties(
        height=500
    ).configure_view(
        strokeWidth=0
    ).configure_legend(
        orient='bottom',
        title=None,
        labelFontSize=12,
        symbolSize=100
    )

    st.altair_chart(chart, width="stretch")

    # Display intersection information
    if intersections:
        st.subheader("Breakeven Points:")
        for i, inter in enumerate(intersections, 1):
            st.write(f"**Point {i}:** Both options earn **{inter['points']:,.0f} points** when non-rent spending is **${inter['non_rent']:,.2f}**")
else:
    st.warning("Please enter a monthly rent greater than 0 to see the chart.")


