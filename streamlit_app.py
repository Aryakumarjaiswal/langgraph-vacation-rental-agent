import streamlit as st

st.set_page_config(
    page_title="StayOps",
    page_icon=":material/apartment:",
    layout="wide",
)

if "guest_user" not in st.session_state:
    st.session_state.guest_user = None
if "ops_user" not in st.session_state:
    st.session_state.ops_user = None
if "guest_messages" not in st.session_state:
    st.session_state.guest_messages = []
if "ops_messages" not in st.session_state:
    st.session_state.ops_messages = []
if "guest_session_id" not in st.session_state:
    st.session_state.guest_session_id = None
if "guest_handoff" not in st.session_state:
    st.session_state.guest_handoff = None
if "guest_pending" not in st.session_state:
    st.session_state.guest_pending = None
if "ops_pending" not in st.session_state:
    st.session_state.ops_pending = None


page = st.navigation(
    [
        st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("app_pages/guest.py", title="Guest", icon=":material/person:"),
        st.Page("app_pages/ops.py", title="Ops", icon=":material/admin_panel_settings:"),
    ],
    position="top",
)
page.run()
