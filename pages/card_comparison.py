import streamlit as st
import pandas as pd
import altair as alt
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import (
    COLORS, CARD_COLORS, CARD_DATA, CARD_NAMES,
    DEFAULT_CPP, DEFAULT_RENT, DEFAULT_NON_RENT, DEFAULT_RENT_DAY_PCT,
    CPP_OPTIONS,
)
from utils.calculations import calculate_card_annual_value, find_best_config_for_card
from utils.charts import get_brand_css

st.set_page_config(
    layout="wide",
    page_title="Card Comparison | Bilt Calculator",
    page_icon=":material/grouped_bar_chart:",
)

# Show loading indicator immediately
loading_placeholder = st.empty()
loading_placeholder.info("Loading Card Comparison...")

# Apply brand CSS
st.markdown(get_brand_css(), unsafe_allow_html=True)

st.title("Card Comparison")

# Clear loading indicator once content starts rendering
loading_placeholder.empty()
st.markdown("Compare all Bilt credit cards to find the best option for your spending habits.")

# Default spending breakdown percentages
DEFAULT_DINING_PCT = 0.25
DEFAULT_GROCERY_PCT = 0.30
DEFAULT_TRAVEL_PCT = 0.15
DEFAULT_OTHER_PCT = 0.30

# --- INPUTS ---
st.subheader("Your Monthly Spending")

# Simple/Advanced toggle
advanced_mode = st.toggle("Advanced Mode", value=False, help="Show detailed spending categories and additional options")

# Initialize session state for all widget keys on first run
if 'simple_rent' not in st.session_state:
    st.session_state.simple_rent = DEFAULT_RENT
if 'simple_non_rent' not in st.session_state:
    st.session_state.simple_non_rent = DEFAULT_NON_RENT
if 'adv_rent' not in st.session_state:
    st.session_state.adv_rent = DEFAULT_RENT
if 'adv_dining' not in st.session_state:
    st.session_state.adv_dining = DEFAULT_NON_RENT * DEFAULT_DINING_PCT
if 'adv_grocery' not in st.session_state:
    st.session_state.adv_grocery = DEFAULT_NON_RENT * DEFAULT_GROCERY_PCT
if 'adv_travel' not in st.session_state:
    st.session_state.adv_travel = DEFAULT_NON_RENT * DEFAULT_TRAVEL_PCT
if 'adv_other' not in st.session_state:
    st.session_state.adv_other = DEFAULT_NON_RENT * DEFAULT_OTHER_PCT
if 'prev_advanced_mode' not in st.session_state:
    st.session_state.prev_advanced_mode = None

# Handle mode transition BEFORE widgets render
if st.session_state.prev_advanced_mode is not None and advanced_mode != st.session_state.prev_advanced_mode:
    if advanced_mode:
        # Switching TO advanced mode - copy simple values to advanced widgets
        st.session_state.adv_rent = st.session_state.simple_rent
        st.session_state.adv_dining = st.session_state.simple_non_rent * DEFAULT_DINING_PCT
        st.session_state.adv_grocery = st.session_state.simple_non_rent * DEFAULT_GROCERY_PCT
        st.session_state.adv_travel = st.session_state.simple_non_rent * DEFAULT_TRAVEL_PCT
        st.session_state.adv_other = st.session_state.simple_non_rent * DEFAULT_OTHER_PCT
    else:
        # Switching TO simple mode - aggregate advanced values back to simple
        st.session_state.simple_rent = st.session_state.adv_rent
        st.session_state.simple_non_rent = (
            st.session_state.adv_dining +
            st.session_state.adv_grocery +
            st.session_state.adv_travel +
            st.session_state.adv_other
        )

st.session_state.prev_advanced_mode = advanced_mode

if not advanced_mode:
    # Simple mode: just rent and total non-rent
    col1, col2, col3 = st.columns(3)

    with col1:
        monthly_rent = st.number_input(
            "Monthly Rent/Mortgage ($)",
            key="simple_rent",
            min_value=0.0,
            step=100.0,
            help="Your monthly rent or mortgage payment"
        )

    with col2:
        total_non_rent = st.number_input(
            "Monthly Non-Rent Spending ($)",
            key="simple_non_rent",
            min_value=0.0,
            step=100.0,
            help="Using breakdown of 25% dining, 30% grocery, 15% travel, 30% other. Choose Advanced mode to customize."
        )

    with col3:
        cpp_choice = st.selectbox(
            "Point Value",
            options=list(CPP_OPTIONS.keys()),
            index=1,  # Default to 1.5 cpp
            help="How much you value Bilt points (cents per point)"
        )
        if cpp_choice == "Custom":
            cpp = st.number_input("Custom cpp", min_value=0.5, max_value=100.0, value=1.5, step=0.1)
        else:
            cpp = CPP_OPTIONS[cpp_choice]

    # Default distribution for simple mode
    dining = total_non_rent * DEFAULT_DINING_PCT
    grocery = total_non_rent * DEFAULT_GROCERY_PCT
    travel = total_non_rent * DEFAULT_TRAVEL_PCT
    other = total_non_rent * DEFAULT_OTHER_PCT

    # Default advanced options
    rent_day_pct = DEFAULT_RENT_DAY_PCT
    include_signup = True
    use_hotel_credits = True
    palladium_meets_min_spend = True
    bilt_cash_value = 1.0
    obsidian_3x_choice = None  # Will be auto-optimized

    # Simple mode: auto-optimize to find best config
    simple_mode_auto = True

    st.text(body="Simple mode auto calculates best rent option for you to get maximum net value. It also auto calculate best 3X choice for Obsidian's Dining or Grocery. It redeems Bilt Cash to maximize rent points. It also assumes you'll be able to fully redeem any left over Bilt Cash if any, hotel credits and meet $4k spend to earn 50,000 bonus poins for Palladium.")

else:
    # Advanced mode: detailed inputs
    simple_mode_auto = False

    st.markdown("##### Spending Categories")
    col1, col2 = st.columns(2)

    with col1:
        monthly_rent = st.number_input(
            "Monthly Rent/Mortgage ($)",
            key="adv_rent",
            min_value=0.0,
            step=100.0,
        )
        dining = st.number_input(
            "Monthly Dining ($)",
            key="adv_dining",
            min_value=0.0,
            step=50.0,
        )
        grocery = st.number_input(
            "Monthly Groceries ($)",
            key="adv_grocery",
            min_value=0.0,
            step=50.0,
        )

    with col2:
        travel = st.number_input(
            "Monthly Travel ($)",
            key="adv_travel",
            min_value=0.0,
            step=50.0,
        )
        other = st.number_input(
            "Monthly Other ($)",
            key="adv_other",
            min_value=0.0,
            step=50.0,
        )
        total_non_rent = dining + grocery + travel + other
        st.metric("Total Non-Rent", f"${total_non_rent:,.0f}")

    st.markdown("##### Point Valuation")
    col1, col2, col3 = st.columns(3)

    with col1:
        cpp_choice = st.selectbox(
            "Point Value",
            options=list(CPP_OPTIONS.keys()),
            index=1,
        )
        if cpp_choice == "Custom":
            cpp = st.number_input("Custom cpp", min_value=0.5, max_value=100.0, value=1.5, step=0.1)
        else:
            cpp = CPP_OPTIONS[cpp_choice]

    with col2:
        bilt_cash_value = st.slider(
            "Bilt Cash Valuation",
            min_value=0.1,
            max_value=1.0,
            value=1.0,
            step=0.1,
            help="1.0 = you can spend all Bilt Cash \$ for \$. Lower if you can't use it all."
        )

    with col3:
        rent_day_pct = st.slider(
            "% Non-Rent on Rent Day",
            min_value=0.0,
            max_value=100.0,
            value=DEFAULT_RENT_DAY_PCT,
            step=1.0,
            help="For Bilt 1.0 reference: What percentage of your non-rent spending happens on the 1st (rent day)? Bilt 1.0 earns 2X on rent day."
        )

    st.markdown("##### Card Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        rent_option = st.radio(
            "Rent Points Option",
            options=[1, 2],
            format_func=lambda x: "Option 1 (Tier-based)" if x == 1 else "Option 2 (Bilt Cash)",
            horizontal=True,
            help="How rent points are calculated for Bilt 2.0 cards",
            key="rent_option"
        )

        # Show sub-option only when Option 2 is selected
        if rent_option == 2:
            convert_bilt_cash_to_rent = st.checkbox(
                "Convert Bilt Cash to rent points",
                value=True,
                help="If unchecked, you keep all 4% Bilt Cash but don't earn rent points"
            )
        else:
            convert_bilt_cash_to_rent = True  # Not relevant for Option 1

    with col2:
        obsidian_3x_choice = st.radio(
            "Obsidian 3X Category",
            options=["dining", "grocery"],
            format_func=lambda x: "3X Dining (no cap)" if x == "dining" else "3X Grocery ($25K cap)",
            horizontal=True,
            help="Obsidian gives 3X on either dining or grocery, not both"
        )

    with col3:
        include_signup = st.checkbox("Include Year 1 Sign-up Bonus", value=True)
        use_hotel_credits = st.checkbox("Will Use Hotel Credits", value=True)
        palladium_meets_min_spend = st.checkbox("Will Meet Palladium Min Spend", value=True,
            help="Required to earn the 50,000 point welcome bonus ($4K in 3 months)")

st.divider()

# --- CALCULATIONS ---
with st.spinner("Calculating card values..."):
    if simple_mode_auto:
        # Simple mode: find best config for each card
        results = []
        for card in CARD_NAMES:
            result = find_best_config_for_card(
                rent=monthly_rent,
                dining=dining,
                grocery=grocery,
                travel=travel,
                other=other,
                card=card,
                cpp=cpp,
                rent_day_pct=rent_day_pct,
                include_signup=include_signup,
                use_hotel_credits=use_hotel_credits,
                palladium_meets_min_spend=palladium_meets_min_spend,
                bilt_cash_value=bilt_cash_value,
            )
            results.append(result)
    else:
        # Advanced mode: use specified config
        results = []
        for card in CARD_NAMES:
            result = calculate_card_annual_value(
                rent=monthly_rent,
                dining=dining,
                grocery=grocery,
                travel=travel,
                other=other,
                card=card,
                rent_option=rent_option,
                cpp=cpp,
                rent_day_pct=rent_day_pct,
                include_signup=include_signup,
                use_hotel_credits=use_hotel_credits,
                palladium_meets_min_spend=palladium_meets_min_spend,
                obsidian_3x_choice=obsidian_3x_choice,
                bilt_cash_value=bilt_cash_value,
                convert_bilt_cash_to_rent=convert_bilt_cash_to_rent,
            )
            results.append(result)

    df = pd.DataFrame(results)

# Find best card (excluding Bilt 1.0 - it's only for reference)
df_2_0 = df[df['card'] != 'Bilt 1.0']
best_idx = df_2_0['net_value'].idxmax()
best_card = df_2_0.loc[best_idx, 'card']
best_value = df_2_0.loc[best_idx, 'net_value']
best_result = df_2_0.loc[best_idx]

# Build recommendation details for simple mode
if simple_mode_auto:
    best_rent_option = best_result['rent_option']
    best_obsidian_choice = best_result['obsidian_3x_choice']

    rent_option_text = "Option 1 (Tier-based)" if best_rent_option == 1 else "Option 2 (Bilt Cash)"

    if best_card == "Obsidian" and best_obsidian_choice:
        obsidian_text = "3X Dining" if best_obsidian_choice == "dining" else "3X Grocery"
        config_text = f"Best with: {rent_option_text}, {obsidian_text}"
    else:
        config_text = f"Best with: {rent_option_text}"
else:
    config_text = ""

# --- RECOMMENDATION BANNER ---
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            padding: 24px; border-radius: 12px; margin-bottom: 24px;">
    <p style="color: #94A3B8; margin: 0 0 8px 0; font-size: 14px;">RECOMMENDED FOR YOU</p>
    <h2 style="color: #0891B2; margin: 0 0 8px 0; font-size: 32px;">{best_card}</h2>
    <p style="color: white; margin: 0; font-size: 20px;">
        <span style="font-family: 'Fira Code', monospace; font-weight: 700;">${best_value:,.0f}</span>
        net annual value
    </p>
    {"<p style='color: #94A3B8; margin: 8px 0 0 0; font-size: 14px;'>" + config_text + "</p>" if config_text else ""}
</div>
""", unsafe_allow_html=True)

# --- COMPARISON TABLE ---
st.subheader("Card Comparison")

# Create display dataframe
display_df = df[['card', 'annual_fee', 'all_points', 'points_value', 'effective_bilt_cash', 'hotel_credit', 'net_value']].copy()
display_df.columns = ['Card', 'Annual Fee', 'Total Points', 'Points Value', 'Bilt Cash', 'Hotel Credit', 'Net Value']

# Format for display
for col in ['Annual Fee', 'Points Value', 'Bilt Cash', 'Hotel Credit', 'Net Value']:
    display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
display_df['Total Points'] = display_df['Total Points'].apply(lambda x: f"{x:,.0f}")

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Card": st.column_config.TextColumn("Card", width="medium"),
        "Net Value": st.column_config.TextColumn("Net Value", width="small"),
    }
)

# Bilt 1.0 reference note
st.caption("*Bilt 1.0 card is included for reference comparison. It will be discontinued after Feb 7, 2025.")

# --- BAR CHART ---
st.subheader("Net Annual Value by Card")

chart = alt.Chart(df).mark_bar(
    cornerRadiusEnd=6,
).encode(
    x=alt.X('net_value:Q',
            title='Net Annual Value ($)',
            axis=alt.Axis(format='$,.0f')),
    y=alt.Y('card:N',
            title=None,
            sort='-x'),
    color=alt.Color('card:N',
                   scale=alt.Scale(
                       domain=list(CARD_COLORS.keys()),
                       range=list(CARD_COLORS.values())
                   ),
                   legend=None),
    tooltip=[
        alt.Tooltip('card:N', title='Card'),
        alt.Tooltip('net_value:Q', title='Net Value', format='$,.2f'),
        alt.Tooltip('all_points:Q', title='Total Points', format=','),
        alt.Tooltip('effective_bilt_cash:Q', title='Bilt Cash', format='$,.2f'),
    ]
).properties(
    height=200
)

# Value labels
text = chart.mark_text(
    align='left',
    baseline='middle',
    dx=5,
    fontWeight='bold',
    fontSize=14,
).encode(
    text=alt.Text('net_value:Q', format='$,.0f'),
    color=alt.value(COLORS['charcoal'])
)

st.altair_chart(chart + text, width="stretch")

# ------ Points Breakdown by Category
st.subheader("Points Breakdown by Category")

# Prepare data for stacked bar
breakdown_data = []
for _, row in df.iterrows():
    breakdown_data.append({'card': row['card'], 'category': 'Rent', 'points': row['rent_points']})
    # For Bilt 1.0, separate out base points and rent day bonus
    if row['card'] == 'Bilt 1.0' and row['rent_day_bonus_points'] > 0:
        # Base points (without rent day bonus)
        base_dining = row['dining_points'] - (row['rent_day_bonus_points'] * row['dining_points'] / (row['dining_points'] + row['grocery_points'] + row['travel_points'] + row['other_points'])) if row['total_non_rent_points'] > 0 else 0
        breakdown_data.append({'card': row['card'], 'category': 'Dining', 'points': row['dining_points'] - row['rent_day_bonus_points'] * (row['dining_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else row['dining_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Grocery', 'points': row['grocery_points'] - row['rent_day_bonus_points'] * (row['grocery_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else row['grocery_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Travel', 'points': row['travel_points'] - row['rent_day_bonus_points'] * (row['travel_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else row['travel_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Other', 'points': row['other_points'] - row['rent_day_bonus_points'] * (row['other_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else row['other_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Rent Day 2X Bonus', 'points': row['rent_day_bonus_points']})
    else:
        breakdown_data.append({'card': row['card'], 'category': 'Dining', 'points': row['dining_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Grocery', 'points': row['grocery_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Travel', 'points': row['travel_points']})
        breakdown_data.append({'card': row['card'], 'category': 'Other', 'points': row['other_points']})
    if row['signup_points'] > 0:
        breakdown_data.append({'card': row['card'], 'category': 'Sign-up Bonus', 'points': row['signup_points']})

breakdown_df = pd.DataFrame(breakdown_data)

category_colors = {
    'Rent': COLORS['teal'],
    'Dining': COLORS['orange'],
    'Grocery': COLORS['green'],
    'Travel': COLORS['purple'],
    'Other': COLORS['gray'],
    'Rent Day 2X Bonus': COLORS['red'],
    'Sign-up Bonus': COLORS['amber'],
}

# Define the category order
category_order = ['Rent', 'Dining', 'Grocery', 'Travel', 'Other', 'Rent Day 2X Bonus', 'Sign-up Bonus']

stacked_chart = alt.Chart(breakdown_df).mark_bar().encode(
    x=alt.X('sum(points):Q',
            title='Annual Points',
            scale=alt.Scale(nice=True),
            axis=alt.Axis(format=',.0f', labelLimit=200)),
    y=alt.Y('card:N',
            title=None,
            sort=list(CARD_COLORS.keys())),
    color=alt.Color('category:N',
                    title='Category',
                    scale=alt.Scale(
                        domain=category_order,  # Use the ordered list here
                        range=[category_colors[cat] for cat in category_order]  # Match colors to order
                    ),
                    sort=category_order,  # Add sort here to control legend order
                    legend=alt.Legend(orient='bottom')),
    order=alt.Order('category_sort:Q'),  # Reference a new calculated field
    tooltip=[
        alt.Tooltip('card:N', title='Card'),
        alt.Tooltip('category:N', title='Category'),
        alt.Tooltip('points:Q', title='Points', format=','),
    ]
).transform_calculate(
    category_sort=f"indexof({category_order}, datum.category)"  # Calculate sort order
).properties(
    height=250
)

# Add total points labels at end of each bar
totals_df = breakdown_df.groupby('card')['points'].sum().reset_index()
totals_df.columns = ['card', 'total_points']

total_labels = alt.Chart(totals_df).mark_text(
    align='left',
    baseline='middle',
    dx=5,
    fontWeight='bold',
    fontSize=12,
).encode(
    x=alt.X('total_points:Q'),
    y=alt.Y('card:N', sort=list(CARD_COLORS.keys())),
    text=alt.Text('total_points:Q', format=',.0f'),
    color=alt.value(COLORS['charcoal'])
)

st.altair_chart(stacked_chart + total_labels, width="stretch")

# --- DETAILED BREAKDOWN (Expandable) ---
with st.expander("View Detailed Breakdown"):
    for num, row in df.iterrows():
        st.markdown(f"### {row['card']}")

        if row['card'] != "Bilt 1.0":
            rent_opt_label = "Option 1" if row['rent_option'] == 1 else "Option 2"
            if row['card'] == "Obsidian" and row['obsidian_3x_choice']:
                obs_label = "3X Dining" if row['obsidian_3x_choice'] == "dining" else "3X Grocery"
                st.caption(f"Using: {rent_opt_label}, {obs_label}")
            else:
                st.caption(f"Using: {rent_opt_label}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Points**")
            if row['rent_points_from_bonus_cash'] > 0:
                st.write(f"Rent: {row['rent_points']:,.0f} ({row['rent_points_from_4pct']:,.0f} from 4% + {row['rent_points_from_bonus_cash']:,.0f} from other Bilt Cash)")
            elif row['rent_points_from_4pct'] > 0:
                st.write(f"Rent: {row['rent_points']:,.0f} ({row['rent_points_from_4pct']:,.0f} from 4%)")
            else:
                st.write(f"Rent: {row['rent_points']:,.0f} ({row['rent_points']/12:,.0f}/mo)")
            st.write(f"Non-Rent Total: {row['total_non_rent_points']:,.0f} ({row['total_non_rent_points']/12:,.0f}/mo)")
            # For Bilt 1.0, show base rates and rent day bonus separately
            if row['card'] == 'Bilt 1.0' and row['rent_day_bonus_points'] > 0:
                # Show base points (what you'd earn at normal multipliers)
                base_non_rent = row['total_non_rent_points'] - row['rent_day_bonus_points']
                dining_base = row['dining_points'] - row['rent_day_bonus_points'] * (row['dining_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else 0
                grocery_base = row['grocery_points'] - row['rent_day_bonus_points'] * (row['grocery_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else 0
                travel_base = row['travel_points'] - row['rent_day_bonus_points'] * (row['travel_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else 0
                other_base = row['other_points'] - row['rent_day_bonus_points'] * (row['other_points'] / row['total_non_rent_points']) if row['total_non_rent_points'] > 0 else 0
                st.write(f"&nbsp;∟ Dining ({row['dining_multiplier']}x): {dining_base:,.0f} ({dining_base/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Grocery ({row['grocery_multiplier']}x): {grocery_base:,.0f} ({grocery_base/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Travel ({row['travel_multiplier']}x): {travel_base:,.0f} ({travel_base/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Other ({row['other_multiplier']}x): {other_base:,.0f} ({other_base/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Rent Day 2X Bonus: {row['rent_day_bonus_points']:,.0f} ({row['rent_day_bonus_points']/12:,.0f}/mo)")
            else:
                st.write(f"&nbsp;∟ Dining ({row['dining_multiplier']}x): {row['dining_points']:,.0f} ({row['dining_points']/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Grocery ({row['grocery_multiplier']}x): {row['grocery_points']:,.0f} ({row['grocery_points']/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Travel ({row['travel_multiplier']}x): {row['travel_points']:,.0f} ({row['travel_points']/12:,.0f}/mo)")
                st.write(f"&nbsp;∟ Other ({row['other_multiplier']}x): {row['other_points']:,.0f} ({row['other_points']/12:,.0f}/mo)")
            if row['signup_points'] > 0:
                st.write(f"Sign-up Bonus: {row['signup_points']:,.0f}")
            st.write(f"**Total: {row['all_points']:,.0f} ({row['all_points']/12:,.0f}/mo)**")

        with col2:
            st.markdown("**Bilt Cash**")
            if row['bilt_cash_4pct'] > 0:
                if row['bilt_cash_4pct_used_for_rent'] > 0:
                    pts_from_4pct = row['rent_points_from_4pct']
                    st.write(f"4% on purchases: \${row['bilt_cash_4pct']:,.2f} (-\${row['bilt_cash_4pct_used_for_rent']:,.2f} for {pts_from_4pct:,.0f} rent pts)")
                else:
                    st.write(f"4% on purchases: ${row['bilt_cash_4pct']:,.2f}")
            else:
                if row['card'] == "Bilt 1.0":
                    st.write("N/A (Bilt 1.0)")
                elif row['rent_option'] == 1:
                    st.write("$0 (Option 1 selected)")
                else:
                    st.write("$0 (No non-rent spending)")
            # $50 per 25K bonus not applicable to Bilt 1.0
            if row['card'] != "Bilt 1.0":
                if row['bilt_cash_25k_used_for_rent'] > 0:
                    pts_from_25k = row['bilt_cash_25k_used_for_rent'] * 100 / 3
                    st.write(f"\$50 per 25K pts: \${row['bilt_cash_25k_total']:,.2f} (-\${row['bilt_cash_25k_used_for_rent']:,.2f} for {pts_from_25k:,.0f} rent pts)")
                else:
                    st.write(f"\$50 per 25K pts: ${row['bilt_cash_25k_bonus']:,.2f}")
            if row['signup_cash'] > 0:
                if row['signup_cash_remaining'] < row['signup_cash']:
                    used = row['signup_cash'] - row['signup_cash_remaining']
                    pts_from_signup = used * 100 / 3
                    st.write(f"Sign-up bonus: \${row['signup_cash']:,.2f} (-\${used:,.2f} for {pts_from_signup:,.0f} rent pts)")
                else:
                    st.write(f"Sign-up bonus: \${row['signup_cash']:,.2f}")
            if row['annual_bilt_cash'] > 0:
                if row['annual_bilt_cash_remaining'] < row['annual_bilt_cash']:
                    used = row['annual_bilt_cash'] - row['annual_bilt_cash_remaining']
                    pts_from_annual = used * 100 / 3
                    st.write(f"Annual benefit: \${row['annual_bilt_cash']:,.2f} (-\${used:,.2f} for {pts_from_annual:,.0f} rent pts)")
                else:
                    st.write(f"Annual benefit: \${row['annual_bilt_cash']:,.2f}")
            st.write(f"**Total: ${row['total_bilt_cash']:,.2f}**")
            if bilt_cash_value < 1.0:
                st.write(f"Effective (@ {bilt_cash_value:.0%}): ${row['effective_bilt_cash']:,.2f}")

        with col3:
            st.markdown("**Value Summary**")
            st.write(f"Points value: ${row['points_value']:,.2f}")
            st.write(f"Bilt Cash: ${row['effective_bilt_cash']:,.2f}")
            st.write(f"Hotel Credit: ${row['hotel_credit']:,.2f}")
            st.write(f"Annual Fee: -${row['annual_fee']:,.2f}")
            st.write(f"**Net Value: ${row['net_value']:,.2f}**")

        if num != len(df)-1:
            # print("JACK:", num,)
            st.divider()
