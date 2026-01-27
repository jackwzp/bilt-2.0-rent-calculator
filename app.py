import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Bilt Calculator",
    page_icon=":material/credit_card:",
    initial_sidebar_state="expanded",
)

# Apply brand CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

#MainMenu, header, footer {visibility: hidden;}
/* Keep the sidebar toggle button visible */
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
}
[data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
}



.stApp {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    color: #0F172A;
    font-weight: 700;
}

.stNumberInput input, .stTextInput input {
    font-family: 'Fira Code', monospace;
}

[data-testid="stMetricValue"] {
    font-family: 'Fira Code', monospace;
    color: #0891B2;
}

.stButton > button {
    background-color: #0891B2;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #0E7490;
}
</style>
""", unsafe_allow_html=True)

PAGE_TITLE = {
    "persona": "Persona Summary",
    "card": "Card Comparison",
    "rent": "Rent Calculator",
    "range": "Range Analysis"
}

# Define main page (this file) with custom title
def run_main():
    # Main landing page
    st.title("Bilt Credit Card Calculator")



    persona = f"""**:material/person_heart: {PAGE_TITLE["persona"]}**
    See the best card for pre-defined personas such as 🍽️ Foodie, ✈️ Traveler and more. Easiest way to start exploring."""

    card = f"""**:material/grouped_bar_chart: {PAGE_TITLE["card"]}**
    Compare all 4 Bilt cards (Bilt 1.0, Blue, Obsidian, Palladium) based on your spending.
    See which card gives you the best net annual value."""

    rent = f"""**:material/calculate: {PAGE_TITLE["rent"]}**
    Compare the two rent point earning methods (Option 1: Tier-based vs Option 2: Bilt Cash).
    Find the breakeven points for your rent amount."""

    range = f"""**:material/map: {PAGE_TITLE["range"]}**
    If your non-rent spend falls within a range, use this tool to see how different card value changes."""


    about = """**About the Bilt 2.0 Cards:**

    | Card | Fee | Dining | Grocery | Travel | Other | Sign Up Bonus | Hotel Credit | Annual Bilt Cash |
    |------|-----|--------|---------|--------|-------|---------|--------|--------|
    | Blue | $0 | 1X | 1X | 1X | 1X | $100 Bilt Cash | $0 | $0 |
    | Obsidian | $95 | 3X* | 3X* | 2X | 1X | $200 Bilt Cash | $100 | $0 |
    | Palladium | $495 | 2X | 2X | 2X | 2X | $300 BC + 50K pts | $400 | $200 |

    \*Obsidian card only gives 3x on either Dining or Grocery, not both. Grocery 3x is capped at $25K.

    All 2.0 cards earn 4% Bilt Cash on everyday purchases (when you select option 2) + $50 per 25K points earned towards elite status."""

    st.markdown(f"""
    Welcome to the Bilt Calculator! This tool helps you compare Bilt credit cards and find the best option for your spending habits.

    ### Available Tools

    👈 **Select a page from the sidebar to get started!**

    {persona}

    {card}

    {rent}

    {range}

    ---
    {about}
    """)

# Define pages with custom url_path
p0 = st.Page(run_main, title="Home", icon=":material/home:", default=True)
p1 = st.Page("pages/persona_breakdown.py", title=PAGE_TITLE["persona"], url_path="persona", icon=":material/person_heart:")
p2 = st.Page("pages/card_comparison.py", title=PAGE_TITLE["card"], url_path="card_comparison", icon=":material/grouped_bar_chart:")
p3 = st.Page("pages/rent_calculator.py", title=PAGE_TITLE["rent"], url_path="rent_calculator", icon=":material/calculate:")
p4 = st.Page("pages/range_analysis.py", title=PAGE_TITLE["range"], url_path="range_analysis", icon=":material/map:")

# Navigate and run selected page
pg = st.navigation([p0, p1, p2, p3, p4])  # Default is first page
pg.run()