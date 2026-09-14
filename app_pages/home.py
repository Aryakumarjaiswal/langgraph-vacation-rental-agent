import streamlit as st

st.title("StayOps")
st.caption("Help for your stay, and tools for our team.")

guest, ops = st.columns(2)
with guest:
    with st.container(border=True):
        st.subheader("Guests")
        st.write(
            "Sign in with your email and password to ask about your booking — "
            "wifi, parking, check-in, and more."
        )
        if st.button("Continue as guest", icon=":material/person:", type="primary", key="home_guest"):
            st.switch_page("app_pages/guest.py")

with ops:
    with st.container(border=True):
        st.subheader("Team")
        st.write(
            "For staff only. Ask about bookings, guests, and earnings in plain language."
        )
        if st.button("Continue as team", icon=":material/analytics:", key="home_ops"):
            st.switch_page("app_pages/ops.py")
