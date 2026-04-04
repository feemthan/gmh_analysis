from typing import Any, Dict, List

import requests
import streamlit as st

# -----------------------------
# Config
# -----------------------------
API_URL = "http://localhost:5000/chat"
REQUEST_TIMEOUT = 120
PAGE_TITLE = "Senior Full Stack Engineer (GenAI-Labs) Take-Home Assignment"


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title=PAGE_TITLE, page_icon="💬", layout="wide")


# -----------------------------
# Session state
# -----------------------------
def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None


init_state()


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: #0f172a;
        color: #e2e8f0;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 8rem;
    }

    .chat-shell {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .hero-wrap {
        min-height: 68vh;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        text-align: center;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.6rem;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        max-width: 700px;
        margin-bottom: 1.2rem;
    }

    .messages-wrap {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .msg-row {
        display: flex;
        width: 100%;
    }

    .msg-row.user {
        justify-content: flex-end;
    }

    .msg-row.assistant {
        justify-content: center;
    }

    .bubble {
        border-radius: 18px;
        padding: 0.9rem 1rem;
        line-height: 1.5;
        box-shadow: 0 8px 24px rgba(0,0,0,0.16);
        word-wrap: break-word;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
    }

    .bubble.user {
        max-width: 52%;
        background: #2563eb;
        color: white;
        text-align: left;
    }

    .bubble.assistant {
        max-width: 72%;
        background: #111827;
        color: #e5e7eb;
        border: 1px solid #1f2937;
    }

    .answer-card {
        background: #0b1220;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-top: 0.6rem;
    }

    .section-label {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .composer-shell {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(to top, rgba(15,23,42,0.98), rgba(15,23,42,0.92));
        backdrop-filter: blur(6px);
        z-index: 999;
        border-top: 1px solid #1e293b;
        padding: 0.8rem 0 1rem 0;
    }

    .composer-inner {
        max-width: 1100px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    div[data-testid="stTextInputRootElement"] input {
        background: #111827 !important;
        color: #e5e7eb !important;
        border-radius: 14px !important;
        border: 1px solid #334155 !important;
        padding-top: 0.8rem !important;
        padding-bottom: 0.8rem !important;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 14px;
        height: 3rem;
        background: #2563eb;
        color: white;
        border: none;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background: #1d4ed8;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Backend call
# -----------------------------
def call_chat_api(user_prompt: str) -> Dict[str, Any]:
    payload = {
        "query": user_prompt,
        "runs": 1,
    }
    response = requests.post(API_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


# -----------------------------
# Helpers
# -----------------------------
def render_assistant_payload(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return str(payload)

    parts: List[str] = []

    answer = payload.get("answer") or payload.get("message") or payload.get("response")
    if answer:
        parts.append(str(answer))

    sql = payload.get("sql")
    if sql:
        parts.append(f"SQL generated:\n{sql}")

    error = payload.get("error")
    if error:
        parts.append(f"Error: {error}")

    if not parts:
        parts.append("Received response from backend.")

    return "\n\n".join(parts)


# -----------------------------
# Send callback
# -----------------------------
def on_send():
    text = st.session_state.chat_input_box.strip()
    if text:
        st.session_state.pending_prompt = text
        st.session_state.chat_input_box = ""


# -----------------------------
# Process pending prompt
# -----------------------------
if st.session_state.pending_prompt:
    prompt_to_send = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt_to_send,
        }
    )

    with st.spinner("Generating response..."):
        try:
            api_json = call_chat_api(prompt_to_send)
            assistant_text = render_assistant_payload(api_json)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "json": api_json,
                }
            )
        except requests.HTTPError as e:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"HTTP error from backend: {e}",
                    "json": {"error": str(e)},
                }
            )
        except requests.RequestException as e:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Backend connection error: {e}",
                    "json": {"error": str(e)},
                }
            )
        except Exception as e:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Unexpected error: {e}",
                    "json": {"error": str(e)},
                }
            )

    st.rerun()


# -----------------------------
# Header controls
# -----------------------------
st.markdown(f"### {PAGE_TITLE}")

# -----------------------------
# Main area
# -----------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-title">Ask anything about your data</div>
            <div class="hero-subtitle">
                Type a question below. The backend will generate SQL and return a JSON response that is shown in the chat.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="messages-wrap">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            st.markdown(
                f'''
                <div class="msg-row user">
                    <div class="bubble user">{content}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'''
                <div class="msg-row assistant">
                    <div class="bubble assistant">{content}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            if "json" in msg:
                with st.expander("View raw JSON", expanded=False):
                    st.json(msg["json"])

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Bottom composer
# -----------------------------
st.markdown(
    '<div class="composer-shell"><div class="composer-inner">',
    unsafe_allow_html=True,
)

input_col, send_col = st.columns([8, 1])
with input_col:
    st.text_input(
        "Message",
        value="",
        placeholder="Ask a question like: How does gaming addiction level vary between genders?",
        label_visibility="collapsed",
        key="chat_input_box",
        on_change=on_send,
    )
with send_col:
    st.button("Send", on_click=on_send, use_container_width=True)

st.markdown("</div></div>", unsafe_allow_html=True)
