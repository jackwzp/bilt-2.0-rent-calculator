import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import (
    COLORS, CARD_COLORS, CARD_NAMES_2_0,
    DEFAULT_CPP, DEFAULT_RENT, CPP_OPTIONS,
)
from utils.calculations import calculate_card_annual_value
from utils.charts import get_brand_css

st.set_page_config(
    layout="wide",
    page_title="Range Analysis | Bilt Calculator",
    page_icon=":material/map:",
)

# Show loading indicator immediately
loading_placeholder = st.empty()
loading_placeholder.info("Loading Range Analysis...")

# Apply brand CSS
st.markdown(get_brand_css(), unsafe_allow_html=True)

# Clear loading indicator once content starts rendering
loading_placeholder.empty()

# Title with Beta badge
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0;">
    <h1 style="margin: 0; padding: 0;">Range Analysis</h1>
    <span title="There may be some bugs - use at your own risk" style="
        background: #EF4444;
        color: white;
        font-size: 12px;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: help;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    ">Beta</span>
</div>
""", unsafe_allow_html=True)
st.markdown("""
See how your non-rent spend range affects different card values.
""")

# --- SETTINGS ---
st.subheader("Settings")

# Spending Category Breakdown section
st.markdown("##### Spending Category Breakdown")
st.caption("Adjust how your non-rent spending is distributed across categories. Must sum to 100%.")

# Initialize session state for category percentages
if 'dining_pct' not in st.session_state:
    st.session_state.dining_pct = 25
if 'grocery_pct' not in st.session_state:
    st.session_state.grocery_pct = 30
if 'travel_pct' not in st.session_state:
    st.session_state.travel_pct = 15
if 'other_pct' not in st.session_state:
    st.session_state.other_pct = 30

col1, col2, col3, col4 = st.columns(4)

with col1:
    dining_pct = st.number_input(
        "Dining %",
        min_value=0,
        max_value=100,
        value=st.session_state.dining_pct,
        step=5,
        key="dining_input"
    )

with col2:
    grocery_pct = st.number_input(
        "Grocery %",
        min_value=0,
        max_value=100,
        value=st.session_state.grocery_pct,
        step=5,
        key="grocery_input"
    )

with col3:
    travel_pct = st.number_input(
        "Travel %",
        min_value=0,
        max_value=100,
        value=st.session_state.travel_pct,
        step=5,
        key="travel_input"
    )

with col4:
    other_pct = st.number_input(
        "Other %",
        min_value=0,
        max_value=100,
        value=st.session_state.other_pct,
        step=5,
        key="other_input"
    )

# Calculate total and show warning if not 100%
total_pct = dining_pct + grocery_pct + travel_pct + other_pct

if total_pct != 100:
    st.warning(f"Category percentages sum to {total_pct}%. Please adjust to equal 100%.")
    # Normalize percentages for calculations
    if total_pct > 0:
        dining_pct_norm = dining_pct / total_pct * 100
        grocery_pct_norm = grocery_pct / total_pct * 100
        travel_pct_norm = travel_pct / total_pct * 100
        other_pct_norm = other_pct / total_pct * 100
    else:
        dining_pct_norm = grocery_pct_norm = travel_pct_norm = other_pct_norm = 25
else:
    dining_pct_norm = dining_pct
    grocery_pct_norm = grocery_pct
    travel_pct_norm = travel_pct
    other_pct_norm = other_pct

# Card Options section
st.markdown("##### Card Options")
col1, col2, col3 = st.columns(3)

with col1:
    rent_option = st.radio(
        "Rent Points Option",
        options=[1, 2],
        format_func=lambda x: "Option 1 (Tier-based)" if x == 1 else "Option 2 (Bilt Cash)",
        horizontal=True,
        help="How rent points are calculated for Bilt 2.0 cards"
    )

    # Show sub-option only when Option 2 is selected
    if rent_option == 2:
        convert_bilt_cash_to_rent = st.checkbox(
            "Convert Bilt Cash to rent points",
            value=True,
            help="If unchecked, you keep all 4% Bilt Cash but don't earn rent points"
        )
    else:
        convert_bilt_cash_to_rent = True

with col2:
    obsidian_3x_choice = st.radio(
        "Obsidian 3X Category",
        options=["dining", "grocery"],
        format_func=lambda x: "3X Dining (no cap)" if x == "dining" else "3X Grocery ($25K cap)",
        horizontal=True,
        help="Obsidian gives 3X on either dining or grocery, not both"
    )

with col3:
    include_signup = st.checkbox("Include Year 1 Sign-up Bonus", value=False)
    use_hotel_credits = st.checkbox("Will Use Hotel Credits", value=True)
    palladium_meets_min_spend = st.checkbox("Palladium Min Spend Met", value=True,
        help="Required to earn the 50,000 point welcome bonus ($4K in 3 months)")

# Point Valuation section
st.markdown("##### Point Valuation")
col1, col2 = st.columns(2)

with col1:
    cpp_choice = st.selectbox(
        "Point Value",
        options=list(CPP_OPTIONS.keys()),
        index=1,
        help="How much you value Bilt points (cents per point)"
    )
    if cpp_choice == "Custom":
        cpp = st.number_input("Custom cpp", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
    else:
        cpp = CPP_OPTIONS[cpp_choice]

with col2:
    bilt_cash_value = st.slider(
        "Bilt Cash Valuation",
        min_value=0.1,
        max_value=1.0,
        value=1.0,
        step=0.1,
        help="1.0 = you can spend all Bilt Cash $ for $. Lower if you can't use it all."
    )

# Visual breakdown bar
breakdown_data = pd.DataFrame({
    'category': ['Dining', 'Grocery', 'Travel', 'Other'],
    'percentage': [dining_pct, grocery_pct, travel_pct, other_pct],
    'color': [COLORS['orange'], COLORS['green'], COLORS['purple'], COLORS['gray']]
})

breakdown_chart = alt.Chart(breakdown_data).mark_bar().encode(
    x=alt.X('percentage:Q', stack='normalize', title=None, axis=None),
    color=alt.Color('category:N',
                   scale=alt.Scale(
                       domain=['Dining', 'Grocery', 'Travel', 'Other'],
                       range=[COLORS['orange'], COLORS['green'], COLORS['purple'], COLORS['gray']]
                   ),
                   legend=alt.Legend(orient='bottom', title=None)),
    tooltip=[
        alt.Tooltip('category:N', title='Category'),
        alt.Tooltip('percentage:Q', title='Percentage', format='.0f'),
    ]
).properties(height=30)

st.altair_chart(breakdown_chart, width="stretch")

st.divider()

# --- YOUR RENT INPUT ---
st.subheader("Rent and Spending Range")
col1, col2 = st.columns(2)

with col1:
    your_rent = st.number_input(
        "Monthly Rent ($)",
        min_value=0.0,
        value=DEFAULT_RENT,
        step=100.0,
        help="Enter your monthly rent to see which card is best at different spending levels"
    )

with col2:
    max_non_rent = st.number_input(
        "Max Non-Rent Spend ($)",
        min_value=500.0,
        value=5000.0,
        step=500.0,
        help="Upper bound for non-rent spending range to analyze"
    )


def generate_data_at_rent(
    rent: float,
    cpp: float,
    rent_option: int,
    include_signup: bool,
    use_hotel_credits: bool,
    palladium_meets_min_spend: bool,
    bilt_cash_value: float,
    obsidian_3x_choice: str,
    convert_bilt_cash_to_rent: bool,
    dining_pct: float,
    grocery_pct: float,
    travel_pct: float,
    other_pct: float,
    max_non_rent: float = 5000,
    num_points: int = 200,
):
    """Generate card values for a specific rent across non-rent spending range."""
    non_rents = np.linspace(0, max_non_rent, num_points)

    results = []
    for non_rent in non_rents:
        # Distribute non-rent spending based on user percentages
        dining = non_rent * (dining_pct / 100)
        grocery = non_rent * (grocery_pct / 100)
        travel = non_rent * (travel_pct / 100)
        other = non_rent * (other_pct / 100)

        best_card = None
        best_value = float('-inf')
        all_values = {}

        for card in CARD_NAMES_2_0:
            result = calculate_card_annual_value(
                rent=rent,
                dining=dining,
                grocery=grocery,
                travel=travel,
                other=other,
                card=card,
                rent_option=rent_option,
                cpp=cpp,
                rent_day_pct=0,  # Not relevant for Bilt 2.0 cards
                include_signup=include_signup,
                use_hotel_credits=use_hotel_credits,
                palladium_meets_min_spend=palladium_meets_min_spend,
                bilt_cash_value=bilt_cash_value,
                obsidian_3x_choice=obsidian_3x_choice,
                convert_bilt_cash_to_rent=convert_bilt_cash_to_rent,
            )
            all_values[card] = result['net_value']
            if result['net_value'] > best_value:
                best_value = result['net_value']
                best_card = card

        results.append({
            'non_rent': non_rent,
            'best_card': best_card,
            'best_value': best_value,
            **{f'{card}_value': v for card, v in all_values.items()}
        })

    return pd.DataFrame(results)


@st.cache_data
def generate_optimizer_grid(
    cpp: float,
    rent_option: int,
    include_signup: bool,
    use_hotel_credits: bool,
    palladium_meets_min_spend: bool,
    bilt_cash_value: float,
    obsidian_3x_choice: str,
    convert_bilt_cash_to_rent: bool,
    dining_pct: float,
    grocery_pct: float,
    travel_pct: float,
    other_pct: float,
    max_rent: int = 6000,
    max_non_rent: int = 5000,
    grid_size: int = 50,
):
    """Generate grid of best card at each rent/spending combination (Bilt 2.0 cards only)."""
    rents = np.linspace(500, max_rent, grid_size)
    non_rents = np.linspace(100, max_non_rent, grid_size)

    results = []
    for rent in rents:
        for non_rent in non_rents:
            # Distribute non-rent spending based on user percentages
            dining = non_rent * (dining_pct / 100)
            grocery = non_rent * (grocery_pct / 100)
            travel = non_rent * (travel_pct / 100)
            other = non_rent * (other_pct / 100)

            best_card = None
            best_value = float('-inf')
            all_values = {}

            for card in CARD_NAMES_2_0:
                result = calculate_card_annual_value(
                    rent=rent,
                    dining=dining,
                    grocery=grocery,
                    travel=travel,
                    other=other,
                    card=card,
                    rent_option=rent_option,
                    cpp=cpp,
                    rent_day_pct=0,  # Not relevant for Bilt 2.0 cards
                    include_signup=include_signup,
                    use_hotel_credits=use_hotel_credits,
                    palladium_meets_min_spend=palladium_meets_min_spend,
                    bilt_cash_value=bilt_cash_value,
                    obsidian_3x_choice=obsidian_3x_choice,
                    convert_bilt_cash_to_rent=convert_bilt_cash_to_rent,
                )
                all_values[card] = result['net_value']
                if result['net_value'] > best_value:
                    best_value = result['net_value']
                    best_card = card

            results.append({
                'rent': rent,
                'non_rent': non_rent,
                'best_card': best_card,
                'best_value': best_value,
                **{f'{card}_value': v for card, v in all_values.items()}
            })

    return pd.DataFrame(results)


# Generate data at user's exact rent
if your_rent > 0:
    with st.spinner("Calculating best card ranges..."):
        df_at_rent = generate_data_at_rent(
            rent=your_rent,
            cpp=cpp,
            rent_option=rent_option,
            include_signup=include_signup,
            use_hotel_credits=use_hotel_credits,
            palladium_meets_min_spend=palladium_meets_min_spend,
            bilt_cash_value=bilt_cash_value,
            obsidian_3x_choice=obsidian_3x_choice,
            convert_bilt_cash_to_rent=convert_bilt_cash_to_rent,
            dining_pct=dining_pct_norm,
            grocery_pct=grocery_pct_norm,
            travel_pct=travel_pct_norm,
            other_pct=other_pct_norm,
            max_non_rent=max_non_rent,
        )

    # --- PERSONALIZED RECOMMENDATION ---
    st.subheader("Best Card by Non-Rent Spend Range")

    # Create filtered colors for Bilt 2.0 cards only
    CARD_COLORS_2_0 = {k: v for k, v in CARD_COLORS.items() if k in CARD_NAMES_2_0}

    # Consolidate ranges by card
    df_sorted = df_at_rent.sort_values('non_rent').reset_index(drop=True)

    # Build ranges for each card
    card_ranges = {card: [] for card in CARD_NAMES_2_0}
    current_card = None
    range_start = None
    prev_non_rent = None

    for idx, row in df_sorted.iterrows():
        if row['best_card'] != current_card:
            # Close previous range
            if current_card is not None and range_start is not None and prev_non_rent is not None:
                card_ranges[current_card].append((range_start, prev_non_rent))
            # Start new range
            current_card = row['best_card']
            range_start = row['non_rent']
        prev_non_rent = row['non_rent']

    # Close the last range
    if current_card is not None and range_start is not None:
        card_ranges[current_card].append((range_start, prev_non_rent))

    # # Display recommendation summary
    # st.markdown(f"""
    # <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    #             padding: 20px; border-radius: 12px; margin-bottom: 20px;">
    #     <p style="color: #94A3B8; margin: 0 0 8px 0; font-size: 14px;">AT ${your_rent:,.0f}/MONTH RENT</p>
    #     <p style="color: white; margin: 0; font-size: 16px;">
    #         Best card by non-rent spending level:
    #     </p>
    # </div>
    # """, unsafe_allow_html=True)

    # Show consolidated ranges per card
    has_ranges = any(card_ranges[card] for card in CARD_NAMES_2_0)

    if has_ranges:
        for card in CARD_NAMES_2_0:
            ranges = card_ranges[card]
            if ranges:
                card_color = CARD_COLORS_2_0.get(card, '#666')
                range_texts = []
                for start, end in ranges:
                    if end >= max_non_rent * 0.98:  # Near max
                        range_texts.append(f"${start:,.0f}+")
                    elif abs(start - end) < 50:  # Very small range
                        range_texts.append(f"~${start:,.0f}")
                    else:
                        range_texts.append(f"${start:,.0f} - ${end:,.0f}")

                ranges_display = "; ".join(range_texts)
                st.markdown(f"""
                <div style="background: {card_color}; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: white; font-size: 16px; font-weight: bold;">{card}</span>
                    <span style="color: white; font-size: 16px; opacity: 0.9;">{ranges_display} (Best Non-Rent Range)</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Fallback: show best card at different spending levels
        st.warning("Unable to calculate ranges. See the chart below for card comparison.")

    st.markdown("")

    # Chart: Card value comparison at user's rent level
    st.markdown(f"##### Net Annual Value by Non-Rent Spending (at ${your_rent:,.0f}/mo rent)")

    # Prepare data for line chart
    line_data = []
    for _, row in df_sorted.iterrows():
        for card in CARD_NAMES_2_0:
            line_data.append({
                'non_rent': row['non_rent'],
                'card': card,
                'value': row[f'{card}_value']
            })
    line_df = pd.DataFrame(line_data)

    # Create interactive selection for hover
    nearest = alt.selection_point(
        nearest=True,
        on='mouseover',
        fields=['non_rent'],
        empty=False
    )

    # Create zoom/pan selection with x-axis limits
    zoom = alt.selection_interval(
        bind='scales',
        encodings=['x', 'y'],
    )

    # Calculate y-axis range from data
    min_value = line_df['value'].min()
    max_value = line_df['value'].max()
    y_padding = (max_value - min_value) * 0.1  # 10% padding

    # Base chart with clamped x-axis (no negative values)
    base = alt.Chart(line_df).encode(
        x=alt.X('non_rent:Q',
                title='Monthly Non-Rent Spending ($)',
                scale=alt.Scale(domain=[0, max_non_rent], clamp=True),
                axis=alt.Axis(format='$,.0f')),
    )

    # Line chart
    lines = base.mark_line(strokeWidth=3).encode(
        y=alt.Y('value:Q',
                title='Net Annual Value ($)',
                scale=alt.Scale(domain=[min_value - y_padding, max_value + y_padding]),
                axis=alt.Axis(format='$,.0f')),
        color=alt.Color('card:N',
                       title='Card',
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       ),
                       legend=alt.Legend(orient='bottom')),
    )

    # Points that appear on hover (with selection parameter)
    points = base.mark_point(size=100, filled=True).encode(
        y=alt.Y('value:Q',
                scale=alt.Scale(domain=[min_value - y_padding, max_value + y_padding])),
        color=alt.Color('card:N',
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       )),
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip('non_rent:Q', title='Monthly Non-Rent', format='$,.0f'),
            alt.Tooltip('card:N', title='Card'),
            alt.Tooltip('value:Q', title='Net Annual Value', format='$,.0f'),
        ]
    ).add_params(nearest).add_params(zoom)

    # Combine layers
    chart = alt.layer(lines, points).properties(
        height=400
    )

    st.altair_chart(chart, width="stretch")

    st.caption("""
    **How to read this chart:** Hover to see exact values. Scroll to zoom, drag to pan.
    The card with the highest line at your spending level gives you the best value.
    Double-click to reset zoom.
    """)

st.divider()

# --- FULL HEATMAP ---
st.subheader("Full Spending Analysis")

st.markdown("""
This heatmap shows which card wins across all rent and spending combinations.
Your rent level is highlighted with a horizontal line.
""")

# Generate heatmap data
with st.spinner("Calculating optimal cards across spending scenarios..."):
    df = generate_optimizer_grid(
        cpp=cpp,
        rent_option=rent_option,
        include_signup=include_signup,
        use_hotel_credits=use_hotel_credits,
        palladium_meets_min_spend=palladium_meets_min_spend,
        bilt_cash_value=bilt_cash_value,
        obsidian_3x_choice=obsidian_3x_choice,
        convert_bilt_cash_to_rent=convert_bilt_cash_to_rent,
        dining_pct=dining_pct_norm,
        grocery_pct=grocery_pct_norm,
        travel_pct=travel_pct_norm,
        other_pct=other_pct_norm,
        max_non_rent=int(max_non_rent),
    )

# Create filtered colors for Bilt 2.0 cards only
CARD_COLORS_2_0 = {k: v for k, v in CARD_COLORS.items() if k in CARD_NAMES_2_0}

# Create heatmap
heatmap = alt.Chart(df).mark_rect().encode(
    x=alt.X('non_rent:Q',
            title='Monthly Non-Rent Spending ($)',
            scale=alt.Scale(domain=[0, max_non_rent]),
            axis=alt.Axis(format='$,.0f', labelAngle=0)),
    y=alt.Y('rent:Q',
            title='Monthly Rent ($)',
            scale=alt.Scale(domain=[500, 6000]),
            axis=alt.Axis(format='$,.0f')),
    color=alt.Color('best_card:N',
                   title='Best Card',
                   scale=alt.Scale(
                       domain=list(CARD_COLORS_2_0.keys()),
                       range=list(CARD_COLORS_2_0.values())
                   ),
                   legend=alt.Legend(
                       orient='bottom',
                       direction='horizontal',
                       titleAnchor='middle',
                   )),
    tooltip=[
        alt.Tooltip('rent:Q', title='Monthly Rent', format='$,.0f'),
        alt.Tooltip('non_rent:Q', title='Monthly Non-Rent', format='$,.0f'),
        alt.Tooltip('best_card:N', title='Best Card'),
        alt.Tooltip('best_value:Q', title='Net Annual Value', format='$,.0f'),
    ]
).properties(
    width=700,
    height=450,
)

# Add horizontal line for user's rent
if your_rent > 0:
    rent_line = alt.Chart(pd.DataFrame({'rent': [your_rent]})).mark_rule(
        color='white',
        strokeWidth=2,
        strokeDash=[5, 5]
    ).encode(
        y='rent:Q'
    )

    # Add label for the rent line
    rent_label = alt.Chart(pd.DataFrame({'rent': [your_rent], 'non_rent': [100], 'label': [f'Your rent: ${your_rent:,.0f}']})).mark_text(
        align='left',
        baseline='bottom',
        dy=-5,
        fontSize=12,
        fontWeight='bold',
        color='white'
    ).encode(
        x='non_rent:Q',
        y='rent:Q',
        text='label:N'
    )

    st.altair_chart(heatmap + rent_line + rent_label, width="stretch")
else:
    st.altair_chart(heatmap, width="stretch")

st.caption("""
**How to read this heatmap:** Each colored region shows where a particular card gives the best value.
- **X-axis**: Your monthly non-rent spending (dining, grocery, travel, other)
- **Y-axis**: Your monthly rent
- **Colors**: The best card for that combination of rent and spending
- **Dashed line**: Your selected rent level
""")

# --- CARD TERRITORY SUMMARY ---
st.subheader("Card Territory Analysis")

# Calculate what percentage of scenarios each card wins
card_wins = df['best_card'].value_counts(normalize=True) * 100

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

for i, card in enumerate(CARD_NAMES_2_0):
    with cols[i]:
        pct = card_wins.get(card, 0)
        st.metric(
            label=card,
            value=f"{pct:.1f}%",
            help=f"{card} is the best choice in {pct:.1f}% of spending scenarios"
        )

# --- KEY INSIGHTS ---
st.subheader("Key Insights")

# Generate insights based on user's rent
insights = []

if your_rent > 0:
    low_threshold = min(1000, max_non_rent * 0.2)
    high_threshold = min(2500, max_non_rent * 0.5)

    low_spend = df_at_rent[df_at_rent['non_rent'] <= low_threshold]
    mid_spend = df_at_rent[(df_at_rent['non_rent'] > low_threshold) & (df_at_rent['non_rent'] <= high_threshold)]
    high_spend = df_at_rent[df_at_rent['non_rent'] > high_threshold]

    if not low_spend.empty:
        best_low = low_spend['best_card'].mode().iloc[0] if len(low_spend['best_card'].mode()) > 0 else low_spend.iloc[0]['best_card']
        insights.append(f"**Low spender** (< ${low_threshold:,.0f}/mo non-rent): {best_low} is typically best")

    if not mid_spend.empty:
        best_mid = mid_spend['best_card'].mode().iloc[0] if len(mid_spend['best_card'].mode()) > 0 else mid_spend.iloc[0]['best_card']
        insights.append(f"**Medium spender** (${low_threshold:,.0f}-${high_threshold:,.0f}/mo non-rent): {best_mid} is typically best")

    if not high_spend.empty:
        best_high = high_spend['best_card'].mode().iloc[0] if len(high_spend['best_card'].mode()) > 0 else high_spend.iloc[0]['best_card']
        insights.append(f"**High spender** (> ${high_threshold:,.0f}/mo non-rent): {best_high} is typically best")

for insight in insights:
    st.markdown(f"- {insight}")
