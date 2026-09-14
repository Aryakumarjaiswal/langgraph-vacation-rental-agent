import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv

from agents.ops_graph import ask_ops
from services.ops_metrics import load_booking_kpis
from services.session_service import append_chat, start_session

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip()

st.title("Team workspace")
st.caption("Ask about bookings, guests, and earnings in everyday language.")

user = st.session_state.get("ops_user")
st.session_state.setdefault("ops_pending", None)

if user is None:
    left, card, right = st.columns([1, 1.2, 1])
    with card:
        with st.container(border=True):
            st.subheader("Staff sign in")
            with st.form("ops_login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign in", icon=":material/login:", type="primary"
                )
            if submitted:
                try:
                    with st.spinner("Signing you in..."):
                        response = httpx.post(
                            f"{API_BASE_URL}/api/v1/auth/login",
                            json={"email": email, "password": password},
                            timeout=20,
                        )
                except Exception:
                    st.error("We couldn't reach the sign-in service. Please try again shortly.")
                    st.stop()
                if response.status_code >= 400:
                    st.error("That email or password doesn't look right.")
                else:
                    payload = response.json()["user"]
                    if payload.get("user_role", {}).get("role") != "staff":
                        st.error("Staff access is required for this area.")
                    else:
                        with st.spinner("Opening your workspace..."):
                            st.session_state.ops_user = payload
                            st.session_state.ops_messages = []
                            st.session_state.ops_pending = None
                            st.session_state.ops_session_id = start_session(
                                payload["id"], "staff"
                            )
                        st.rerun()
    st.stop()


def prompt_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return getattr(value, "text", "") or str(value)


status, signout = st.columns([4, 1])
with status:
    st.badge("Staff", icon=":material/verified:", color="blue")
    st.caption(user["email"])
with signout:
    if st.button("Sign out", icon=":material/logout:"):
        st.session_state.ops_user = None
        st.session_state.ops_messages = []
        st.session_state.ops_session_id = None
        st.session_state.ops_pending = None
        st.rerun()

kpis = load_booking_kpis()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bookings", kpis["bookings"])
c2.metric("Commission", kpis["commission"])
c3.metric("Platforms", kpis["platforms"])
c4.metric("Guests", kpis["guests"])

if not st.session_state.ops_messages:
    st.caption("Try asking")
    q1, q2, q3 = st.columns(3)
    if q1.button("Total commission"):
        st.session_state.ops_pending = "What is the total commission collected?"
        st.rerun()
    if q2.button("Bookings by platform"):
        st.session_state.ops_pending = "How many bookings are there per platform?"
        st.rerun()
    if q3.button("Recent guests"):
        st.session_state.ops_pending = "List 5 guest names and their listing titles."
        st.rerun()

chat_box = st.container(height=380, border=True)
with chat_box:
    for msg in st.session_state.ops_messages:
        avatar = ":material/person:" if msg["role"] == "user" else ":material/analytics:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

typed = st.chat_input("Ask about bookings or guests")
prompt = st.session_state.ops_pending or typed
st.session_state.ops_pending = None

if prompt:
    text = prompt_text(prompt)
    if text:
        with st.chat_message("user", avatar=":material/person:"):
            st.write(text)
        with st.chat_message("assistant", avatar=":material/analytics:"):
            with st.spinner("Working on that..."):
                try:
                    result = ask_ops(text)
                    answer = result.get("answer") or "I couldn't find an answer."
                except Exception:
                    answer = "Sorry, something went wrong. Please try again."
            st.write(answer)
        st.session_state.ops_messages.append({"role": "user", "content": text})
        st.session_state.ops_messages.append({"role": "assistant", "content": answer})
        append_chat(st.session_state.ops_session_id, text, answer)
