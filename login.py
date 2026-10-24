import hmac
import base64
from pathlib import Path
import os
import streamlit as st


def show_login():
    """Show a single-admin demo login and return authentication status."""
    if st.session_state.get("ecogrid_logged_in", False):
        return True

    st.markdown(
        '<div class="ecogrid-login-title">🌿 EcoGrid AI</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="ecogrid-login-subtitle">'
        'Predictive Circular-Resource Grid · Secure Campus Access'
        '</div>',
        unsafe_allow_html=True
    )

    # The uploaded campus photo appears only behind the login form.
    # All login labels and inputs have opaque high-contrast surfaces.
    image_path = Path(__file__).resolve().parent / "images" / "login_campus.jpg"
    if image_path.is_file():
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        st.markdown(f"""
        <style>
        div[data-testid="stForm"]:has([data-testid="stTextInput"]) {{
            background-image:
                linear-gradient(180deg, rgba(7,24,37,.38), rgba(7,24,37,.78)),
                url('data:image/jpeg;base64,{encoded}') !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            border: 1px solid rgba(255,255,255,.4) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            box-shadow: 0 12px 30px rgba(0,0,0,.20) !important;
        }}
        div[data-testid="stForm"]:has([data-testid="stTextInput"]) label p {{
            color: #fff !important;
            font-weight: 750 !important;
            text-shadow: 0 2px 4px rgba(0,0,0,.9);
        }}
        div[data-testid="stForm"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] input {{
            background: #ffffff !important;
            color: #172b3a !important;
            -webkit-text-fill-color: #172b3a !important;
            border-radius: 8px !important;
        }}
        div[data-testid="stForm"]:has([data-testid="stTextInput"]) [data-testid="stTextInput"] input::placeholder {{
            color: #697985 !important;
            -webkit-text-fill-color: #697985 !important;
            opacity: 1 !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    st.subheader("Welcome Back")
    st.write("Sign in to access your campus resource dashboard.")

    with st.form("ecogrid_login"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter password"
        )
        submitted = st.form_submit_button(
            "🔐 Login", use_container_width=True
        )

    if submitted:
        expected_user = os.getenv("ECOGRID_USERNAME", "")
        expected_pass = os.getenv("ECOGRID_PASSWORD", "")

        if not expected_user or not expected_pass:
            st.error("Login credentials are not configured.")
        elif (hmac.compare_digest(username, expected_user)
              and hmac.compare_digest(password, expected_pass)):
            st.session_state.ecogrid_logged_in = True
            st.session_state.ecogrid_username = username
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    st.caption("© 2026 EcoGrid AI | Smart Sustainable Campus")
    return False


def show_logout():
    with st.sidebar:
        st.success("🌿 EcoGrid AI")
        st.write("👤 Welcome, " +
                 st.session_state.get("ecogrid_username", "User"))
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
