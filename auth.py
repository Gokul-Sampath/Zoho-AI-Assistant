"""
Corporate ERP Authentication & Access Control Module
Provides role-based access control (RBAC) with two permission tiers:
1. Administrator (Full Access): Access to all ERP modules (Executive Dashboard, Automation, Reference Docs, Settings & Admin Panel, Deluge AI Assistant)
2. Developer (Limited Access): Restricted exclusively to the Deluge AI Assistant.
"""

import streamlit as st
from typing import Dict, Any, Optional

# Pre-configured corporate ERP users
ERP_USERS = {
    "admin": {
        "password": "admin123",
        "name": "Sarah Jenkins",
        "email": "s.jenkins@enterprise.zoho.internal",
        "role": "admin",
        "title": "Lead Systems Architect & ERP Admin",
        "avatar": "🛡️",
        "badge": "Full Access",
        "department": "Enterprise Architecture"
    },
    "developer": {
        "password": "dev123",
        "name": "Alex Rivera",
        "email": "a.rivera@enterprise.zoho.internal",
        "role": "developer",
        "title": "Deluge Application Developer",
        "avatar": "💻",
        "badge": "AI Assistant Only",
        "department": "Creator Solutions"
    }
}


def init_auth_state():
    """Initialize session state authentication variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "llama3_params" not in st.session_state:
        st.session_state.llama3_params = {
            "temperature": 0.2,
            "top_p": 0.9,
            "context_window": 4096,
            "repeat_penalty": 1.15,
            "num_predict": 1536,
            "selected_model": "llama3:8b",
            "ollama_host": "http://localhost:11434"
        }


def authenticate_user(username: str, password: str) -> bool:
    """Validate credentials against ERP user database."""
    username = username.strip().lower()
    if username in ERP_USERS and ERP_USERS[username]["password"] == password:
        st.session_state.authenticated = True
        st.session_state.user_id = username
        st.session_state.user_info = ERP_USERS[username]
        return True
    return False


def logout_user():
    """Clear session authentication state."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_info = None
    if "assistant_messages" in st.session_state:
        st.session_state.assistant_messages = []


def is_admin() -> bool:
    """Check if the currently authenticated user possesses Administrator privileges."""
    if not st.session_state.get("authenticated", False):
        return False
    user = st.session_state.get("user_info", {})
    return user.get("role") == "admin"


def is_authenticated() -> bool:
    """Check if a session is currently authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return dictionary of current user information."""
    return st.session_state.get("user_info")


def require_admin_permission():
    """Call inside views that require Full Access. Halts execution if user is unauthorized."""
    if not is_admin():
        st.error("⛔ **Access Denied**: This module requires **Administrator (Full Access)** privileges.")
        st.info("Your current account is provisioned for **Limited Access (Restricted to Deluge AI Assistant)**. Please contact your ERP administrator to request elevated permissions.")
        st.stop()
