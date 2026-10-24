import streamlit as st


def apply_theme():
    """Apply visual styling and let users switch themes."""
    if "ecogrid_theme" not in st.session_state:
        st.session_state.ecogrid_theme = "Dark"

    with st.sidebar:
        st.markdown("### 🎨 Appearance")
        st.radio(
            "Theme",
            ["Dark", "Light"],
            key="ecogrid_theme",
            horizontal=True,
        )
        st.divider()

    dark = st.session_state.ecogrid_theme == "Dark"
    bg = "#0b1220" if dark else "#f4f8f5"
    surface = "#131f30" if dark else "#ffffff"
    surface_alt = "#1b2b40" if dark else "#e9f3ec"
    text = "#e8f2ee" if dark else "#16291e"
    muted = "#9fb4ae" if dark else "#52695b"
    border = "#304558" if dark else "#d4e4d8"
    accent = "#34d399" if dark else "#15803d"
    field = "#182638" if dark else "#ffffff"

    st.markdown(f"""
    <style>
    :root {{ color-scheme: {"dark" if dark else "light"}; }}
    html, body, [data-testid="stAppViewContainer"],
    .stApp, [data-testid="stMain"] {{
        background: {bg} !important;
        color: {text} !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background: {surface} !important;
        color: {text} !important;
    }}
    [data-testid="stHeader"] {{
        background: {bg} !important;
    }}
    [data-testid="stBottom"] {{
        background: {bg} !important;
    }}
    .block-container {{
        max-width: 1320px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }}
    h1, h2, h3, h4, p, label, li,
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stCaptionContainer"] {{
        color: {text} !important;
    }}
    [data-testid="stCaptionContainer"] p,
    .stCaption, small {{
        color: {muted} !important;
    }}
    h1 {{ font-weight: 800 !important; letter-spacing: -.035em; }}
    h2 {{ border-left: 4px solid {accent}; padding-left: .7rem; }}
    h3 {{ color: {accent} !important; }}
    [data-testid="stMetric"] {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(0,0,0,.045);
    }}
    [data-testid="stMetricValue"] {{
        color: {accent} !important;
        font-weight: 750;
    }}
    [data-testid="stForm"] {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 18px;
        padding: 18px;
    }}
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    [data-baseweb="base-input"],
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input {{
        background: {field} !important;
        color: {text} !important;
        border-color: {border} !important;
    }}
    input, textarea {{ color: {text} !important; }}
    div.stButton > button,
    div.stFormSubmitButton > button {{
        border-radius: 11px;
        border: 1px solid {border};
        font-weight: 650;
        transition: all .15s ease;
    }}
    div.stFormSubmitButton > button {{
        background: #159b58 !important;
        color: white !important;
        border-color: #159b58 !important;
    }}
    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {{
        border-color: {accent} !important;
        box-shadow: 0 3px 12px rgba(34,197,94,.18);
    }}
    [data-testid="stAlert"] {{
        border-radius: 12px;
    }}
    hr {{ border-color: {border} !important; }}
    [data-testid="stRadio"] label {{
        color: {text} !important;
    }}
    .ecogrid-hero {{
        background: linear-gradient(115deg, #075e3d, #0e8270 60%, #14516a);
        border-radius: 20px;
        padding: 27px 30px;
        margin: 8px 0 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,.10);
    }}
    .ecogrid-hero h1 {{
        color: #ffffff !important;
        font-size: clamp(26px, 3vw, 42px);
        margin: 0 0 7px;
    }}
    .ecogrid-hero p {{
        color: #e4fff0 !important;
        margin: 0;
        font-size: 15px;
    }}
    .ecogrid-login-title {{
        text-align: center;
        color: {accent} !important;
        font-size: 44px;
        font-weight: 850;
        letter-spacing: -.04em;
        margin-top: 25px;
    }}
    .ecogrid-login-subtitle {{
        text-align: center;
        color: {muted} !important;
        margin-bottom: 24px;
    }}
    </style>
    """, unsafe_allow_html=True)
    return dark
