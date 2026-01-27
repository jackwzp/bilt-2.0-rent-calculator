"""
Bilt Card Insights Based on Persona

Comprehensive analysis with test personas and actionable recommendations
for different spending patterns.
"""

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

from utils.constants import COLORS, CARD_COLORS, CARD_NAMES_2_0, CARD_DATA, DEFAULT_CPP
from utils.calculations import (
    calculate_card_annual_value,
    find_best_config_for_card,
    calculate_method1_points,
    calculate_method2_points,
)
from utils.charts import get_brand_css, configure_altair_theme

# Page config
st.set_page_config(
    page_title="Bilt Card for You",
    page_icon=":material/person_heart:",
    layout="wide"
)

# Apply brand styling
st.markdown(get_brand_css(), unsafe_allow_html=True)
configure_altair_theme()

# Card colors for 2.0 cards only
CARD_COLORS_2_0 = {k: v for k, v in CARD_COLORS.items() if k in CARD_NAMES_2_0}

# =============================================================================
# TEST SCENARIOS - Different User Personas
# Each scenario includes ALL advanced mode parameters
# =============================================================================

SCENARIOS = {
    "The Newbie": {
        "description": "New to credit cards, wants simplicity, doesn't travel much",
        "emoji": "🐣",
        # Spending
        "rent": 1500,
        "dining": 150,
        "grocery": 250,
        "travel": 50,
        "other": 150,
        # Valuations
        "cpp": 1.0,  # Cashes out points, doesn't optimize transfers
        "bilt_cash_value": 0.8,  # May not use all Bilt Cash
        # Options
        "use_hotel_credits": False,  # Doesn't travel enough to use hotel credits
        "hotel_credit_pct": 0.3,  # 0% utilization
        "palladium_meets_min_spend": False,  # Unlikely to hit $4K in 3 months
        "obsidian_3x_choice": "grocery",  # Home cooking preference
    },
    "Average Renter": {
        "description": "Middle-of-the-road rent and spending - most common situation",
        "emoji": "🏠",
        # Spending
        "rent": 2000,
        "dining": 200,
        "grocery": 300,
        "travel": 100,
        "other": 200,
        # Valuations
        "cpp": 1.5,  # Average transfer value
        "bilt_cash_value": 1.0,  # Can use all Bilt Cash
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 0.5,  # 50% utilization
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",
    },
    "Yuppie": {
        "description": "The Young Professional. Moderate rent, dining-heavy, building credit",
        "emoji": "👔",
        # Spending
        "rent": 1800,
        "dining": 400,
        "grocery": 250,
        "travel": 200,
        "other": 300,
        # Valuations
        "cpp": 1.5,
        "bilt_cash_value": 1.0,
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 0.6,
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",
    },
    "Foodie": {
        "description": "Heavy dining spending - restaurants and delivery enthusiast",
        "emoji": "🍽️",
        # Spending
        "rent": 2000,
        "dining": 800,
        "grocery": 150,
        "travel": 100,
        "other": 200,
        # Valuations
        "cpp": 1.5,
        "bilt_cash_value": 1.0,
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 0.7,
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",  # Obvious choice for foodies
    },
    "Home Cook": {
        "description": "Heavy grocery spending - prefers cooking at home",
        "emoji": "👨‍🍳",
        # Spending
        "rent": 2000,
        "dining": 100,
        "grocery": 600,
        "travel": 100,
        "other": 200,
        # Valuations
        "cpp": 1.5,
        "bilt_cash_value": 1.0,
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 0.5,
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "grocery",  # Obvious choice for home cooks
    },
    "The Traveler": {
        "description": "Heavy travel spending - flights and hotels",
        "emoji": "✈️",
        # Spending
        "rent": 2500,
        "dining": 300,
        "grocery": 300,
        "travel": 800,
        "other": 300,
        # Valuations
        "cpp": 2.0,  # Gets great value from transfers
        "bilt_cash_value": 1.0,
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 1.0,  # Full utilization
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",
    },
    "Minimalist": {
        "description": "Pays rent but minimal other spending",
        "emoji": "🧘",
        # Spending
        "rent": 1200,
        "dining": 50,
        "grocery": 150,
        "travel": 25,
        "other": 75,
        # Valuations
        "cpp": 1.0,  # Simple valuation
        "bilt_cash_value": 0.5,  # Harder to use all Bilt Cash with low spend
        # Options
        "use_hotel_credits": False,
        "hotel_credit_pct": 0.0,
        "palladium_meets_min_spend": False,
        "obsidian_3x_choice": "grocery",
    },
    "Point Maximizer": {
        "description": "Strategic spender who optimizes every purchase for max points",
        "emoji": "🎯",
        # Spending
        "rent": 2500,
        "dining": 500,
        "grocery": 400,
        "travel": 400,
        "other": 400,
        # Valuations
        "cpp": 2.0,  # Maximizes transfer values
        "bilt_cash_value": 1.0,  # Uses every dollar
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 1.0,  # Full utilization
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",  # Will optimize per situation
    },
    "Big Spender": {
        "description": "High rent AND high spending across all categories",
        "emoji": "💎",
        # Spending
        "rent": 5000,
        "dining": 1000,
        "grocery": 800,
        "travel": 600,
        "other": 800,
        # Valuations
        "cpp": 2.0,  # Gets great transfer value
        "bilt_cash_value": 1.0,
        # Options
        "use_hotel_credits": True,
        "hotel_credit_pct": 0.8,
        "palladium_meets_min_spend": True,
        "obsidian_3x_choice": "dining",
    },
}


def run_scenario_analysis(scenario: dict, include_signup: bool = False) -> dict:
    """Run full analysis for a scenario and return results for all Bilt 2.0 cards."""
    results = {}

    # Calculate effective hotel credit based on utilization percentage
    for card in CARD_NAMES_2_0:
        # Get base hotel credit from card data
        base_hotel_credit = CARD_DATA[card]["hotel_credit"]

        # Apply utilization percentage
        if scenario.get("use_hotel_credits", True):
            hotel_credit_pct = scenario.get("hotel_credit_pct", 1.0)
            effective_hotel_credit = base_hotel_credit * hotel_credit_pct
        else:
            effective_hotel_credit = 0

        # Find the best configuration for this card
        best_result = find_best_config_for_card(
            rent=scenario["rent"],
            dining=scenario["dining"],
            grocery=scenario["grocery"],
            travel=scenario["travel"],
            other=scenario["other"],
            card=card,
            cpp=scenario.get("cpp", 1.5),
            rent_day_pct=0,  # Not relevant for Bilt 2.0 cards
            include_signup=include_signup,
            use_hotel_credits=scenario.get("use_hotel_credits", True),
            palladium_meets_min_spend=scenario.get("palladium_meets_min_spend", True),
            bilt_cash_value=scenario.get("bilt_cash_value", 1.0),
        )

        # Adjust hotel credit based on utilization
        if not scenario.get("use_hotel_credits", True):
            best_result["hotel_credit"] = 0
            best_result["net_value"] = (
                best_result["points_value"] +
                best_result["effective_bilt_cash"] -
                best_result["annual_fee"]
            )
        elif scenario.get("hotel_credit_pct", 1.0) < 1.0:
            original_hotel = best_result["hotel_credit"]
            adjusted_hotel = original_hotel * scenario.get("hotel_credit_pct", 1.0)
            best_result["hotel_credit"] = adjusted_hotel
            best_result["net_value"] = (
                best_result["points_value"] +
                best_result["effective_bilt_cash"] +
                adjusted_hotel -
                best_result["annual_fee"]
            )

        results[card] = best_result

    return results


def get_best_card(results: dict) -> tuple:
    """Get the best card and its value from results."""
    best_card = max(results.keys(), key=lambda c: results[c]["net_value"])
    return best_card, results[best_card]["net_value"]


def create_scenario_comparison_chart(all_results: dict, scenario_names: list):
    """Create a grouped bar chart comparing all scenarios."""
    data = []
    for scenario_name in scenario_names:
        for card in CARD_NAMES_2_0:
            data.append({
                "Scenario": scenario_name,
                "Card": card,
                "Net Value": all_results[scenario_name][card]["net_value"]
            })

    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("Scenario:N", title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Net Value:Q", title="Net Annual Value ($)", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Card:N",
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       ),
                       legend=alt.Legend(orient="bottom")),
        xOffset="Card:N",
        tooltip=[
            alt.Tooltip("Scenario:N"),
            alt.Tooltip("Card:N"),
            alt.Tooltip("Net Value:Q", format="$,.0f"),
        ]
    ).properties(
        width=800,
        height=400,
    )

    return chart


def create_winner_summary_chart(winner_data: list, persona_order: list):
    """Create a chart showing which card wins for each scenario."""
    df = pd.DataFrame(winner_data)

    chart = alt.Chart(df).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("Net Value:Q", title="Net Annual Value ($)", axis=alt.Axis(format="$,.0f")),
        y=alt.Y("Persona:N", title=None, sort=persona_order,
                axis=alt.Axis(labelLimit=300)),  # Prevent label truncation
        color=alt.Color("Best Card:N",
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       ),
                       legend=alt.Legend(orient="bottom", title="Winning Card")),
        tooltip=[
            alt.Tooltip("Persona:N"),
            alt.Tooltip("Best Card:N"),
            alt.Tooltip("Best Rent Option:N", title="Rent Option"),
            alt.Tooltip("Net Value:Q", format="$,.0f"),
            alt.Tooltip("Monthly Rent:Q", format="$,.0f"),
            alt.Tooltip("Monthly Non-Rent:Q", format="$,.0f"),
            alt.Tooltip("CPP:Q", format=".1f"),
            alt.Tooltip("Hotel Credit Used:Q", format=".0%"),
        ]
    ).properties(
        width=600,
        height=450,
    )

    # Add value labels
    text = chart.mark_text(
        align="left",
        baseline="middle",
        dx=5,
        fontWeight="bold",
    ).encode(
        text=alt.Text("Net Value:Q", format="$,.0f"),
        color=alt.value(COLORS["charcoal"])
    )

    return chart + text


def create_points_value_sensitivity_chart(scenario: dict, include_signup: bool):
    """Show how card rankings change with different CPP valuations."""
    cpp_range = [1.0, 1.25, 1.5, 1.75, 2.0]
    data = []

    # Create a modified scenario for each CPP value
    for cpp in cpp_range:
        modified_scenario = scenario.copy()
        modified_scenario["cpp"] = cpp
        results = run_scenario_analysis(modified_scenario, include_signup=include_signup)
        for card in CARD_NAMES_2_0:
            data.append({
                "CPP": cpp,
                "Card": card,
                "Net Value": results[card]["net_value"]
            })

    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("CPP:Q", title="Point Value (cents per point)",
                scale=alt.Scale(domain=[1.0, 2.0]),
                axis=alt.Axis(values=cpp_range)),
        y=alt.Y("Net Value:Q", title="Net Annual Value ($)", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Card:N",
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       ),
                       legend=alt.Legend(orient="right")),
        tooltip=[
            alt.Tooltip("CPP:Q", format=".2f"),
            alt.Tooltip("Card:N"),
            alt.Tooltip("Net Value:Q", format="$,.0f"),
        ]
    ).properties(
        width=500,
        height=300,
        title="How Point Valuation Affects Card Rankings"
    )

    return chart


def create_year1_vs_year2_comparison(scenario: dict):
    """Create comparison chart showing Year 1 vs Year 2+ values."""
    data = []

    for year_label, include_signup in [("Year 1 (with bonus)", True), ("Year 2+ (ongoing)", False)]:
        results = run_scenario_analysis(scenario, include_signup=include_signup)
        for card in CARD_NAMES_2_0:
            data.append({
                "Year": year_label,
                "Card": card,
                "Net Value": results[card]["net_value"]
            })

    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("Card:N", title=None),
        y=alt.Y("Net Value:Q", title="Net Annual Value ($)", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Card:N",
                       scale=alt.Scale(
                           domain=list(CARD_COLORS_2_0.keys()),
                           range=list(CARD_COLORS_2_0.values())
                       ),
                       legend=None),
        xOffset="Year:N",
        tooltip=[
            alt.Tooltip("Year:N"),
            alt.Tooltip("Card:N"),
            alt.Tooltip("Net Value:Q", format="$,.0f"),
        ]
    ).properties(
        width=400,
        height=250
    ).facet(
        column=alt.Column("Year:N", title=None)
    )

    return chart


def create_points_breakdown_chart(results: dict, card_names: list):
    """Create a stacked horizontal bar chart showing points breakdown by card.

    Args:
        results: Dict of card results from run_scenario_analysis
        card_names: List of card names to include

    Returns:
        Altair chart object
    """
    points_data = []
    for card in card_names:
        r = results[card]
        points_data.append({
            "card": card,
            "rent_points": r["rent_points"],
            "dining_points": r["dining_points"],
            "grocery_points": r["grocery_points"],
            "travel_points": r["travel_points"],
            "other_points": r["other_points"],
        })

    points_df = pd.DataFrame(points_data)

    # Categories ordered with rent first, then other categories
    categories = ['rent_points', 'dining_points', 'grocery_points', 'travel_points', 'other_points']
    category_labels = {
        'rent_points': 'Rent',
        'dining_points': 'Dining',
        'grocery_points': 'Grocery',
        'travel_points': 'Travel',
        'other_points': 'Other',
    }

    # Category colors - rent first (teal), then others
    category_colors = [COLORS['teal'], COLORS['orange'], COLORS['green'], COLORS['purple'], COLORS['gray']]

    melted = points_df.melt(
        id_vars=['card'],
        value_vars=categories,
        var_name='category',
        value_name='points'
    )
    melted['category_label'] = melted['category'].map(category_labels)

    # Add sort order for categories (rent first)
    category_order = {cat: i for i, cat in enumerate(categories)}
    melted['category_order'] = melted['category'].map(category_order)

    points_chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X('sum(points):Q',
                title='Annual Points',
                axis=alt.Axis(format=',.0f')),  # Use number format, not scientific notation
        y=alt.Y('card:N',
                title=None,
                sort=list(card_names),
                axis=alt.Axis(labelLimit=200)),  # Prevent label truncation
        color=alt.Color('category_label:N',
                       title='Category',
                       scale=alt.Scale(
                           domain=list(category_labels.values()),
                           range=category_colors
                       ),
                       legend=alt.Legend(orient='bottom')),
        order=alt.Order('category_order:Q'),  # Sort by category order (rent first)
        tooltip=[
            alt.Tooltip('card:N', title='Card'),
            alt.Tooltip('category_label:N', title='Category'),
            alt.Tooltip('points:Q', title='Points', format=',.0f'),
        ]
    ).properties(
        height=200
    )

    return points_chart


# =============================================================================
# SIDEBAR SETTINGS
# =============================================================================
st.sidebar.header("Analysis Settings")

# Year 1 vs Year 2 toggle - prominent at top
year_mode = st.sidebar.radio(
    "Which year are you analyzing?",
    options=["Year 1 (with sign-up bonus)", "Year 2+ (ongoing value)"],
    index=0,
    help="Year 1 includes sign-up bonuses. Year 2+ shows ongoing annual value."
)
include_signup = year_mode == "Year 1 (with sign-up bonus)"

if include_signup:
    st.sidebar.info("Sign-up bonuses included: Blue \$100, Obsidian \$200, Palladium \$300 + 50K pts")
else:
    st.sidebar.info("Showing ongoing annual value without sign-up bonuses")

# =============================================================================
# MAIN PAGE
# =============================================================================

st.title("Persona Summary")

st.markdown(f"""
**Notes:**
- Analysis shows **{'Year 1 (with sign-up bonuses)' if include_signup else 'Year 2+ (ongoing value)'}** - toggle in sidebar to switch
- This page uses pre-defined user persona to demonstrate card value across different spending patterns
- All calculations assume optimal rent option selection for each card
- Hotel credits valued based on each persona's utilization percentage
- Each persona has customized assumptions about hotel credit utilization, point valuations, and spending habits.
- Bilt Cash valued based on each persona's ability to use it

*For personalized analysis with your exact spending, use the **Card Comparison** page.*
""")


st.markdown("---")

# Run analysis for all scenarios
all_results = {}
winner_data = []

# Get persona order from SCENARIOS dict for consistent sorting
persona_order = [f"{scenario['emoji']} {name}" for name, scenario in SCENARIOS.items()]

for name, scenario in SCENARIOS.items():
    results = run_scenario_analysis(scenario, include_signup=include_signup)
    all_results[name] = results
    best_card, best_value = get_best_card(results)
    best_rent_option = results[best_card]["rent_option"]
    total_non_rent = scenario["dining"] + scenario["grocery"] + scenario["travel"] + scenario["other"]
    winner_data.append({
        "Persona": f"{scenario['emoji']} {name}",
        "Best Card": best_card,
        "Best Rent Option": f"Option {best_rent_option}",
        "Net Value": best_value,
        "Monthly Rent": scenario["rent"],
        "Monthly Non-Rent": total_non_rent,
        "CPP": scenario.get("cpp", 1.5),
        "Hotel Credit Used": scenario.get("hotel_credit_pct", 1.0) if scenario.get("use_hotel_credits", True) else 0,
    })

# Count wins
win_counts = {}
for item in winner_data:
    card = item["Best Card"]
    win_counts[card] = win_counts.get(card, 0) + 1

# =============================================================================
# SECTION: SCENARIO WINNERS CHART
# =============================================================================

st.header("Best Card for Persona")

winner_chart = create_winner_summary_chart(winner_data, persona_order)
st.altair_chart(winner_chart, width='stretch')

st.markdown("""
**How to read this chart:** Each bar shows the best card for that persona.
The bar length shows how much annual value you'd get with the optimal card choice.
Hover over bars to see detailed assumptions for each persona.
""")

st.subheader("Persona Parameters Reference")

with st.expander("View all persona parameters"):
    st.markdown("""
    Each persona has customized parameters based on the following assumptions and parameters:
    """)

    params_data = []
    for name, scenario in SCENARIOS.items():
        total_non_rent = scenario["dining"] + scenario["grocery"] + scenario["travel"] + scenario["other"]
        params_data.append({
            "Persona": f"{scenario['emoji']} {name}",
            "Rent": f"${scenario['rent']:,}",
            "Dining": f"${scenario['dining']:,}",
            "Grocery": f"${scenario['grocery']:,}",
            "Travel": f"${scenario['travel']:,}",
            "Other": f"${scenario['other']:,}",
            "Total Non-Rent": f"${total_non_rent:,}",
            "CPP": scenario.get("cpp", 1.5),
            "Bilt Cash Value": f"{scenario.get('bilt_cash_value', 1.0):.0%}",
            "Hotel Credit %": f"{scenario.get('hotel_credit_pct', 1.0) if scenario.get('use_hotel_credits', True) else 0:.0%}",
            "Min Spend Met": "Yes" if scenario.get("palladium_meets_min_spend", True) else "No",
            "Obsidian 3X": scenario.get("obsidian_3x_choice", "dining").title(),
        })

    params_df = pd.DataFrame(params_data)
    st.dataframe(params_df, width='stretch', hide_index=True)

st.markdown("---")

# =============================================================================
# SECTION: DETAILED SCENARIO EXPLORER
# =============================================================================

st.header("Explore Persona")

selected_scenario = st.selectbox(
    "Select a persona to explore in detail:",
    options=list(SCENARIOS.keys()),
    format_func=lambda x: f"{SCENARIOS[x]['emoji']} {x} - {SCENARIOS[x]['description']}"
)

scenario = SCENARIOS[selected_scenario]
results = all_results[selected_scenario]
best_card, best_value = get_best_card(results)
best_rent_option = results[best_card]["rent_option"]

# Recommendation banner - full width at top
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
        <div>
            <h3 style="color: #0891B2; margin: 0;">{scenario['emoji']} {selected_scenario}</h3>
            <p style="margin: 5px 0 0 0; color: #94A3B8; font-style: italic;">{scenario['description']}</p>
        </div>
        <div style="text-align: right;">
            <h3 style="color: #0891B2; margin: 0;">Recommended: {best_card}</h3>
            <p style="font-size: 24px; margin: 5px 0; font-family: 'Fira Code', monospace;">
                ${best_value:,.0f}/year net value
            </p>
            <p style="margin: 0; color: #10B981; font-weight: 600;">
                Best Rent Option: {best_rent_option}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Monthly spending and assumptions in tables
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Monthly Spending**")
    total_monthly = scenario['rent'] + scenario['dining'] + scenario['grocery'] + scenario['travel'] + scenario['other']
    total_non_rent = total_monthly - scenario['rent']
    spending_data = pd.DataFrame([
        {"Category": "Rent", "Amount": f"${scenario['rent']:,}"},
        {"Category": "Dining", "Amount": f"${scenario['dining']:,}"},
        {"Category": "Grocery", "Amount": f"${scenario['grocery']:,}"},
        {"Category": "Travel", "Amount": f"${scenario['travel']:,}"},
        {"Category": "Other", "Amount": f"${scenario['other']:,}"},
        {"Category": "Total Monthly", "Amount": f"${total_monthly:,}"},
        {"Category": "Non-Rent Ratio", "Amount": f"{(total_non_rent/scenario['rent'])*100:.0f}% of rent"},
    ])
    st.dataframe(spending_data, width='stretch', hide_index=True)

with col2:
    st.markdown("**Assumptions**")
    hotel_pct = scenario.get('hotel_credit_pct', 1.0) if scenario.get('use_hotel_credits', True) else 0
    assumptions_data = pd.DataFrame([
        {"Parameter": "Point Value", "Value": f"{scenario.get('cpp', 1.5)} cpp"},
        {"Parameter": "Bilt Cash Value", "Value": f"{scenario.get('bilt_cash_value', 1.0):.0%}"},
        {"Parameter": "Hotel Credit Used", "Value": f"{hotel_pct:.0%}"},
        {"Parameter": "Palladium Min Spend Met", "Value": "Yes" if scenario.get("palladium_meets_min_spend", True) else "No"},
        {"Parameter": "Obsidian 3X Choice", "Value": scenario.get("obsidian_3x_choice", "dining").title()},
    ])
    st.dataframe(assumptions_data, width='stretch', hide_index=True)

# Card comparison table
st.markdown("**Card Comparison**")
comparison_data = []
for card in CARD_NAMES_2_0:
    r = results[card]
    comparison_data.append({
        "Card": card,
        "Annual Fee": f"${r['annual_fee']}",
        "Total Points": f"{r['total_points']:,.0f}",
        "Points Value": f"${r['points_value']:,.0f}",
        "Bilt Cash": f"${r['total_bilt_cash']:,.0f}",
        "Hotel Credit": f"${r['hotel_credit']:,.0f}",
        "Net Value": f"${r['net_value']:,.0f}",
    })

df = pd.DataFrame(comparison_data)
st.dataframe(df, width='stretch', hide_index=True)

# Year 1 vs Year 2 comparison for this scenario
st.subheader("Year 1 vs Year 2+ Comparison")

year1_results = run_scenario_analysis(scenario, include_signup=True)
year1_best, year1_value = get_best_card(year1_results)
year2_results = run_scenario_analysis(scenario, include_signup=False)
year2_best, year2_value = get_best_card(year2_results)

# Create comparison table
year_comparison_data = []
for card in CARD_NAMES_2_0:
    y1 = year1_results[card]
    y2 = year2_results[card]
    y1_delta = y1['net_value'] - year1_value
    y2_delta = y2['net_value'] - year2_value
    year_comparison_data.append({
        "Card": card,
        "Year 1 Value": f"${y1['net_value']:,.0f}",
        # "Year 1 vs Best": "BEST" if card == year1_best else f"{y1_delta:+,.0f}",
        "Year 2+ Value": f"${y2['net_value']:,.0f}",
        # "Year 2+ vs Best": "BEST" if card == year2_best else f"{y2_delta:+,.0f}",
        "Difference": f"${y1['net_value'] - y2['net_value']:+,.0f}",
    })

year_comparison_df = pd.DataFrame(year_comparison_data)
st.dataframe(year_comparison_df, width='stretch', hide_index=True)

if year1_best != year2_best:
    st.warning(f"The best card changes between Year 1 ({year1_best}) and Year 2+ ({year2_best})!")

# Points breakdown chart
st.subheader("Points Breakdown by Card")

points_chart = create_points_breakdown_chart(results, CARD_NAMES_2_0)
st.altair_chart(points_chart, width='stretch')


# =============================================================================
# SECTION: POINT VALUATION SENSITIVITY
# =============================================================================

st.header("How Point Valuation Affects Your Choice")

st.markdown("""
The "best" card can change depending on how you value Bilt points:
- **1.0 cpp**: Cash/Statement credit redemption
- **1.5 cpp**: Average transfer partner value
- **2.0 cpp**: Good transfer partner redemption (sweet spots)
""")

sensitivity_chart = create_points_value_sensitivity_chart(scenario, include_signup)
st.altair_chart(sensitivity_chart, width='stretch')
st.markdown("---")

# =============================================================================
# SECTION: ALL SCENARIOS COMPARISON
# =============================================================================

st.header("Full Comparison: All Persona")


# Create comprehensive comparison table
all_data = []
for name, scenario in SCENARIOS.items():
    results = all_results[name]
    best_card, best_value = get_best_card(results)
    total_non_rent = scenario["dining"] + scenario["grocery"] + scenario["travel"] + scenario["other"]

    row = {
        "Persona": f"{scenario['emoji']} {name}",
        "Rent": f"${scenario['rent']:,}",
        "Non-Rent": f"${total_non_rent:,}",
        "Ratio": f"{(total_non_rent/scenario['rent'])*100:.0f}%",
        "CPP": scenario.get("cpp", 1.5),
        "Hotel %": f"{scenario.get('hotel_credit_pct', 1.0) if scenario.get('use_hotel_credits', True) else 0:.0%}",
        "Best Card": best_card,
        "Net Value": f"${best_value:,.0f}",
    }

    # Add each card's value
    for card in CARD_NAMES_2_0:
        row[card] = f"${results[card]['net_value']:,.0f}"

    all_data.append(row)

df = pd.DataFrame(all_data)
st.dataframe(df, width='stretch', hide_index=True)

# Grouped bar chart
st.subheader("Net Annual Value by Card Across All Persona")

all_scenarios_chart = create_scenario_comparison_chart(all_results, list(SCENARIOS.keys()))
st.altair_chart(all_scenarios_chart, width='stretch')


