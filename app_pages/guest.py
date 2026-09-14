import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from agents.guest_graph import ask_guest
from rag.retriever import property_exists
from services.session_service import append_chat, start_session

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").strip()

st.title("Guest help")
st.caption("Ask anything about your stay. We'll use the property linked to your account.")

user = st.session_state.get("guest_user")
st.session_state.setdefault("guest_handoff", None)
st.session_state.setdefault("guest_pending", None)

if user is None:
    left, card, right = st.columns([1, 1.2, 1])
    with card:
        with st.container(border=True):
            st.subheader("Sign in")
            st.caption("Enter the email and password you received for your stay.")
            with st.form("guest_login"):
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
                    st.error("That email or password doesn't look right. Please try again.")
                else:
                    payload = response.json()["user"]
                    if payload.get("user_role", {}).get("role") not in {"guest", "staff"}:
                        st.error("This account can't use guest help.")
                    elif not payload.get("property_id"):
                        st.error(
                            "Your account isn't linked to a stay yet. "
                            "Please contact support."
                        )
                    elif not property_exists(payload["property_id"]):
                        st.error(
                            "We don't have details for your stay yet. "
                            "Please contact support."
                        )
                    else:
                        with st.spinner("Getting things ready..."):
                            st.session_state.guest_user = payload
                            st.session_state.guest_messages = []
                            st.session_state.guest_handoff = None
                            st.session_state.guest_pending = None
                            st.session_state.guest_session_id = start_session(
                                payload["id"], payload["user_role"]["role"]
                            )
                        st.rerun()
    st.stop()


def prompt_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return getattr(value, "text", "") or str(value)


def render_call_card(links: dict) -> None:
    with st.container(border=True):
        st.markdown("**Support**")
        status = links.get("dial_status") or ""
        if status == "dialed":
            st.success("We're calling our support team for you now.")
        elif status == "failed":
            st.warning("We couldn't complete the call right now. Please try again soon.")
        else:
            st.info("We've noted your request. A teammate will help you shortly.")


status, signout = st.columns([4, 1])
with status:
    st.badge("Signed in", icon=":material/check_circle:", color="green")
    st.caption(user["email"])
with signout:
    if st.button("Sign out", icon=":material/logout:"):
        st.session_state.guest_user = None
        st.session_state.guest_messages = []
        st.session_state.guest_session_id = None
        st.session_state.guest_handoff = None
        st.session_state.guest_pending = None
        st.rerun()

if st.session_state.guest_handoff:
    render_call_card(st.session_state.guest_handoff)

if not st.session_state.guest_messages:
    st.caption("Quick questions")
    q1, q2, q3 = st.columns(3)
    if q1.button("Wifi", icon=":material/wifi:"):
        st.session_state.guest_pending = "What are the wifi details?"
        st.rerun()
    if q2.button("Parking", icon=":material/local_parking:"):
        st.session_state.guest_pending = "Where can I park?"
        st.rerun()
    if q3.button("Talk to support", icon=":material/support_agent:"):
        st.session_state.guest_pending = "I want to talk to customer support"
        st.rerun()

chat_box = st.container(height=420, border=True)
with chat_box:
    for msg in st.session_state.guest_messages:
        avatar = ":material/person:" if msg["role"] == "user" else ":material/apartment:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

typed = st.chat_input("Ask about your stay, or ask to talk to support")
prompt = st.session_state.guest_pending or typed
st.session_state.guest_pending = None

if prompt:
    text = prompt_text(prompt)
    if text:
        with st.chat_message("user", avatar=":material/person:"):
            st.write(text)
        with st.chat_message("assistant", avatar=":material/apartment:"):
            with st.spinner("Looking that up for you..."):
                try:
                    result = ask_guest(
                        text,
                        user["property_id"],
                        st.session_state.guest_session_id,
                        history=[
                            HumanMessage(content=item["content"])
                            if item["role"] == "user"
                            else AIMessage(content=item["content"])
                            for item in st.session_state.guest_messages
                        ],
                    )
                    if isinstance(result, str):
                        answer = result
                        transferred = False
                        links = {"dial_status": "", "dial_detail": ""}
                    else:
                        answer = result.get("answer") or ""
                        transferred = bool(result.get("transferred"))
                        links = result.get("call") or {
                            "dial_status": "",
                            "dial_detail": "",
                        }
                except Exception:
                    answer = "Sorry, I couldn't answer that just now. Please try again."
                    transferred = False
                    links = {"dial_status": "", "dial_detail": ""}
            st.write(answer)
        st.session_state.guest_messages.append({"role": "user", "content": text})
        st.session_state.guest_messages.append({"role": "assistant", "content": answer})
        if transferred:
            st.session_state.guest_handoff = links
        append_chat(st.session_state.guest_session_id, text, answer)
