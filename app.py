import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Bilt Calculator",
    page_icon=":material/credit_card:",
    initial_sidebar_state="collapsed",
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

.stSidebar {
            display: none
}
</style>
""", unsafe_allow_html=True)

st.subheader("App has a new home, click button to access.")
st.link_button("Open App", "https://thefintech.dev/bilt")
