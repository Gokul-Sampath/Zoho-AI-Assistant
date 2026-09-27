"""
Zoho Enterprise Suite - Corporate ERP Portal
Master Controller with Role-Based Access Control (RBAC), Executive Styling,
Pristine High-Contrast Text Visibility, and Unified Settings & Admin Panel.
"""

import streamlit as st
import auth

# Application-wide configuration
st.set_page_config(
    page_title="Zoho Enterprise ERP | Deluge Intelligence",
    page_icon="🦎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main Language Model Configuration: Llama 3 8B (Optimized for Low Latency & High Throughput)
DEFAULT_LLM_MODEL = "llama3:8b"

# Initialize Authentication & Shared State
auth.init_auth_state()

# Ensure Llama 3 8B is synchronized as active model
if "llama3_params" in st.session_state:
    st.session_state.llama3_params["selected_model"] = DEFAULT_LLM_MODEL
    # Check Streamlit Community Cloud secrets for remote Ollama host or standalone mode
    try:
        if hasattr(st, "secrets"):
            if "OLLAMA_HOST" in st.secrets and st.secrets["OLLAMA_HOST"]:
                st.session_state.llama3_params["ollama_host"] = st.secrets["OLLAMA_HOST"]
            if "STANDALONE_MODE" in st.secrets:
                st.session_state.llama3_params["standalone_mode"] = bool(st.secrets["STANDALONE_MODE"])
    except Exception:
        pass

# Corporate ERP Global Aesthetics with Pristine High-Contrast Text Visibility
st.markdown("""
<style>
    /* =========================================================
       1. GLOBAL TYPOGRAPHY & HIGH CONTRAST PALETTE
       ========================================================= */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #0f172a !important;
    }
    
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* =========================================================
       2. SIDEBAR HIGH-CONTRAST TEXT & NAVIGATION STYLING
       ========================================================= */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Ensure ALL text inside sidebar is bright and legible */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #f1f5f9;
    }

    /* Section group headers in sidebar */
    [data-testid="stSidebarNavSeparator"] {
        border-color: #334155 !important;
    }
    [data-testid="stSidebarNav"] [data-testid="stSidebarNavHeader"] {
        color: #94a3b8 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        padding-top: 0.75rem !important;
    }

    /* Sidebar Navigation Links */
    [data-testid="stSidebarNav"] a {
        background-color: transparent !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        margin: 2px 0 !important;
        transition: all 0.15s ease-in-out !important;
    }
    [data-testid="stSidebarNav"] a span {
        color: #e2e8f0 !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
    }
    
    /* Hover state */
    [data-testid="stSidebarNav"] a:hover {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebarNav"] a:hover span {
        color: #ffffff !important;
    }

    /* Active / Current Page Navigation Link */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #1e3a8a !important;
        border-left: 4px solid #3b82f6 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* =========================================================
       3. METRIC CARDS & EXECUTIVE TILES
       ========================================================= */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #0f172a !important;
        font-size: 1.55rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #475569 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    /* =========================================================
       4. BUTTONS & INPUT CONTROLS
       ========================================================= */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Sign out button in sidebar */
    .signout-btn > button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
    }
    .signout-btn > button:hover {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        border-color: #ef4444 !important;
    }

    /* Badges */
    .badge-admin {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-dev {
        background: linear-gradient(135deg, #059669, #047857);
        color: #ffffff !important;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# AUTHENTICATION GATEWAY
# ==============================================================================
if not auth.is_authenticated():
    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
    c_pad1, c_login, c_pad2 = st.columns([1, 1.4, 1])

    with c_login:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align: center; margin-bottom: 22px;'>"
                "<div style='font-size: 2.6rem;'>🦎</div>"
                "<h2 style='margin: 0; color: #0f172a; font-weight: 800; letter-spacing: -0.02em;'>ZOHO ENTERPRISE SUITE</h2>"
                "<p style='color: #475569; font-size: 0.95rem; margin-top: 4px;'>Corporate ERP & Deluge Intelligence Platform</p>"
                "</div>",
                unsafe_allow_html=True
            )

            st.markdown("##### 🔐 Sign In to ERP Console")
            
            with st.form("erp_login_form"):
                uname = st.text_input("Username or Corporate ID", placeholder="admin or developer")
                pword = st.text_input("Password", type="password", placeholder="Enter password")
                login_submitted = st.form_submit_button("Sign In to Portal", type="primary", use_container_width=True)

            if login_submitted:
                if auth.authenticate_user(uname, pword):
                    st.success("Authentication successful! Redirecting to ERP workspace...")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Use 'admin' (pass: admin123) or 'developer' (pass: dev123).")

            st.markdown("---")
            st.markdown("##### ⚡ Quick Corporate Demo Access")
            st.caption("One-click authentication to test access levels:")

            c_adm_btn, c_dev_btn = st.columns(2)
            with c_adm_btn:
                if st.button("👑 Admin (Full Access)", use_container_width=True):
                    auth.authenticate_user("admin", "admin123")
                    st.rerun()
            with c_dev_btn:
                if st.button("💻 Developer (Limited)", use_container_width=True):
                    auth.authenticate_user("developer", "dev123")
                    st.rerun()

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            with st.expander("📋 Role Permission Matrix Overview"):
                st.markdown("""
                | Module / Capability | 👑 Administrator (Full Access) | 💻 Developer (Limited Access) |
                | :--- | :---: | :---: |
                | **Minimalist Executive Dashboard** | ✅ Full Visibility & Control | ❌ Restricted |
                | **Deluge AI Assistant** | ✅ Full Access | ✅ Full Access |
                | **On-Demand Documentation (Operations & Data)** | ✅ Full Access & Export | 👁️ Read-Only Virtualized Access |
                | **Automation & Task Scheduling** | ✅ Full Cadence Control | ❌ Restricted |
                | **Settings & Administration Panel** | ✅ Full Access (CMD, Models, Vectors) | ❌ Restricted |
                """)

    st.stop()


# ==============================================================================
# AUTHENTICATED PORTAL: SIDEBAR & DYNAMIC NAVIGATION
# ==============================================================================
user = auth.get_current_user() or {}
is_admin = auth.is_admin()

# Sidebar User Profile Card
with st.sidebar:
    st.markdown(
        f"<div style='border: 1px solid #334155; background: #1e293b; border-radius: 8px; padding: 12px; margin-bottom: 12px;'>"
        f"<div style='display: flex; align-items: center; gap: 10px;'>"
        f"<div style='font-size: 1.8rem;'>{user.get('avatar', '👤')}</div>"
        f"<div>"
        f"<div style='font-weight: 700; color: #ffffff; font-size: 0.95rem;'>{user.get('name')}</div>"
        f"<div style='color: #94a3b8; font-size: 0.75rem;'>{user.get('title')}</div>"
        f"</div>"
        f"</div>"
        f"<div style='margin-top: 10px; display: flex; justify-content: space-between; align-items: center;'>"
        f"<span class='{'badge-admin' if is_admin else 'badge-dev'}'>{user.get('badge')}</span>"
        f"<span style='color: #cbd5e1; font-size: 0.75rem;'>{user.get('department')}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown('<div class="signout-btn">', unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        auth.logout_user()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Active Intelligence Engine Badge
    standalone = False
    try:
        if hasattr(st, "secrets") and st.secrets.get("STANDALONE_MODE", False):
            standalone = True
    except Exception:
        pass

    badge_title = "Built-in Deluge Engine" if standalone else "Llama 3 8B (llama3:8b)"
    badge_subtitle = "Offline Documentation Grounded • Zero Lag" if standalone else "Optimized • Low Latency & Minimal Lag"

    st.markdown(
        f"<div style='border: 1px solid #334155; background: #0f172a; border-radius: 6px; padding: 8px 10px; margin-top: 10px; margin-bottom: 6px;'>"
        f"<div style='font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;'>Active Intelligence Engine</div>"
        f"<div style='font-size: 0.95rem; font-weight: 700; color: #38bdf8;'>⚡ {badge_title}</div>"
        f"<div style='font-size: 0.72rem; color: #94a3b8;'>{badge_subtitle}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")


# Define Module Pages
dashboard_page = st.Page(
    "views/dashboard.py",
    title="Executive Dashboard",
    icon="📊",
    default=is_admin
)

assistant_page = st.Page(
    "views/assistant.py",
    title="Deluge AI Assistant",
    icon="💬",
    default=not is_admin
)

documentation_page = st.Page(
    "views/documentation.py",
    title="On-Demand Documentation",
    icon="📖"
)

scheduler_page = st.Page(
    "views/scheduler.py",
    title="Automation & Schedules",
    icon="⏱️"
)

admin_settings_page = st.Page(
    "views/admin_settings.py",
    title="Settings & Admin Panel",
    icon="⚙️"
)

# Role-Based Dynamic Page Hierarchy
if is_admin:
    # Full Access Administrator: All Enterprise Modules
    nav_structure = {
        "Executive & Control": [dashboard_page, assistant_page],
        "Operations & Data": [documentation_page, scheduler_page],
        "Administration": [admin_settings_page]
    }
else:
    # Limited Access: Restricted to Deluge AI Assistant & On-Demand Reference Documentation under Operations & Data
    nav_structure = {
        "Deluge Intelligence": [assistant_page],
        "Operations & Data": [documentation_page]
    }

# Render Navigation and Run Active Page
navigation = st.navigation(nav_structure)
navigation.run()
