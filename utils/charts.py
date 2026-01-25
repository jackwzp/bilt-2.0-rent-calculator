import altair as alt
from .constants import COLORS, CARD_COLORS


def get_brand_css() -> str:
    """Return CSS for brand styling in Streamlit."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

    /* Hide default Streamlit elements - be specific to avoid hiding sidebar controls */


    /* Typography */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
    }

    /* Number inputs with monospace */
    .stNumberInput input, .stTextInput input {
        font-family: 'Fira Code', monospace;
    }

    /* Metric values */
    [data-testid="stMetricValue"] {
        font-family: 'Fira Code', monospace;
        color: #0891B2;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 8px;
    }

    /* Buttons */
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

    /* Toggle/Checkbox styling */
    .stCheckbox {
        color: #1E293B;
    }

    /* Selectbox */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 6px;
    }

    /* Divider */
    hr {
        border-color: #E2E8F0;
    }

    /* Card-like containers */
    .element-container {
        border-radius: 8px;
    }

    /* Recommendation banner styling */
    .recommendation-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin: 20px 0;
    }

    .recommendation-banner h3 {
        color: #0891B2;
        margin: 0;
    }
    </style>
    """


def configure_altair_theme():
    """Configure Altair with brand theme."""
    alt.themes.register('brand_theme', lambda: {
        'config': {
            'view': {'strokeWidth': 0},
            'axis': {
                'labelFont': 'Inter',
                'titleFont': 'Inter',
                'labelColor': COLORS['gray'],
                'titleColor': COLORS['charcoal'],
                'gridColor': COLORS['gray_light'],
            },
            'legend': {
                'labelFont': 'Inter',
                'titleFont': 'Inter',
                'labelColor': COLORS['charcoal'],
            },
            'title': {
                'font': 'Inter',
                'color': COLORS['charcoal'],
            },
        }
    })
    alt.themes.enable('brand_theme')


def create_card_comparison_chart(data, value_column='net_value'):
    """Create horizontal bar chart comparing card values."""
    # Sort by value descending
    data = data.sort_values(value_column, ascending=True)

    chart = alt.Chart(data).mark_bar(
        cornerRadiusEnd=4,
    ).encode(
        x=alt.X(f'{value_column}:Q',
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
            alt.Tooltip(f'{value_column}:Q', title='Net Value', format='$,.2f'),
        ]
    ).properties(
        height=200
    )

    # Add value labels
    text = chart.mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontWeight='bold',
    ).encode(
        text=alt.Text(f'{value_column}:Q', format='$,.0f'),
        color=alt.value(COLORS['charcoal'])
    )

    return (chart + text).configure_view(strokeWidth=0)


def create_points_breakdown_chart(data):
    """Create stacked bar chart showing points breakdown by category."""
    # Melt the data for stacked chart
    categories = ['rent_points', 'dining_points', 'grocery_points', 'travel_points', 'other_points']
    category_colors = {
        'rent_points': COLORS['teal'],
        'dining_points': COLORS['orange'],
        'grocery_points': COLORS['green'],
        'travel_points': COLORS['purple'],
        'other_points': COLORS['gray'],
    }
    category_labels = {
        'rent_points': 'Rent',
        'dining_points': 'Dining',
        'grocery_points': 'Grocery',
        'travel_points': 'Travel',
        'other_points': 'Other',
    }

    melted = data.melt(
        id_vars=['card'],
        value_vars=categories,
        var_name='category',
        value_name='points'
    )
    melted['category_label'] = melted['category'].map(category_labels)

    chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X('sum(points):Q',
                title='Annual Points',
                axis=alt.Axis(format=',')),
        y=alt.Y('card:N',
                title=None,
                sort=list(CARD_COLORS.keys())),
        color=alt.Color('category_label:N',
                       title='Category',
                       scale=alt.Scale(
                           domain=list(category_labels.values()),
                           range=[category_colors[k] for k in categories]
                       ),
                       legend=alt.Legend(orient='bottom')),
        order=alt.Order('category:N'),
        tooltip=[
            alt.Tooltip('card:N', title='Card'),
            alt.Tooltip('category_label:N', title='Category'),
            alt.Tooltip('points:Q', title='Points', format=','),
        ]
    ).properties(
        height=200
    ).configure_view(strokeWidth=0)

    return chart


def create_optimizer_heatmap(data):
    """Create heatmap showing best card at each rent/spending combination."""
    heatmap = alt.Chart(data).mark_rect().encode(
        x=alt.X('rent:Q',
                title='Monthly Rent ($)',
                bin=alt.Bin(maxbins=50),
                axis=alt.Axis(format='$,.0f')),
        y=alt.Y('non_rent:Q',
                title='Monthly Non-Rent Spending ($)',
                bin=alt.Bin(maxbins=50),
                axis=alt.Axis(format='$,.0f')),
        color=alt.Color('best_card:N',
                       title='Best Card',
                       scale=alt.Scale(
                           domain=list(CARD_COLORS.keys()),
                           range=list(CARD_COLORS.values())
                       ),
                       legend=alt.Legend(orient='bottom')),
        tooltip=[
            alt.Tooltip('rent:Q', title='Rent', format='$,.0f'),
            alt.Tooltip('non_rent:Q', title='Non-Rent', format='$,.0f'),
            alt.Tooltip('best_card:N', title='Best Card'),
            alt.Tooltip('best_value:Q', title='Net Value', format='$,.0f'),
        ]
    ).properties(
        width=600,
        height=500
    ).configure_view(strokeWidth=0)

    return heatmap
