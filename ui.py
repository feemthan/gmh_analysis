from typing import Any, Dict, List
import html

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
    if "is_sending" not in st.session_state:
        st.session_state.is_sending = False


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
        margin-bottom: 0.8rem;
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

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 14px;
        height: 3rem;
        background: #2563eb;
        color: white;
        border: none;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
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


def safe_text(text: Any) -> str:
    return html.escape("" if text is None else str(text))


def append_user_message(text: str) -> None:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
        }
    )


def append_assistant_message(content: str, payload: Dict[str, Any] | None = None) -> None:
    message: Dict[str, Any] = {
        "role": "assistant",
        "content": content,
    }
    if payload is not None:
        message["json"] = payload
    st.session_state.messages.append(message)


def process_prompt(prompt: str) -> None:
    cleaned = prompt.strip()
    if not cleaned:
        return

    if st.session_state.is_sending:
        return

    st.session_state.is_sending = True
    append_user_message(cleaned)

    try:
        with st.spinner("Generating response..."):
            api_json = call_chat_api(cleaned)
        assistant_text = render_assistant_payload(api_json)
        append_assistant_message(assistant_text, api_json)

    except requests.HTTPError as e:
        append_assistant_message(
            f"HTTP error from backend: {e}",
            {"error": str(e)},
        )
    except requests.RequestException as e:
        append_assistant_message(
            f"Backend connection error: {e}",
            {"error": str(e)},
        )
    except Exception as e:
        append_assistant_message(
            f"Unexpected error: {e}",
            {"error": str(e)},
        )
    finally:
        st.session_state.is_sending = False


# -----------------------------
# Header
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

    for _, msg in enumerate(st.session_state.messages):
        role = msg.get("role", "assistant")
        content = safe_text(msg.get("content", ""))

        if role == "user":
            st.markdown(
                f"""
                <div class="msg-row user">
                    <div class="bubble user">{content}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="msg-row assistant">
                    <div class="bubble assistant">{content}</div>
                </div>
                """,
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

with st.form("chat_form", clear_on_submit=True):
    input_col, send_col = st.columns([8, 1])

    with input_col:
        prompt = st.text_input(
            "Message",
            value="",
            placeholder="Ask a question like: How does gaming addiction level vary between genders?",
            label_visibility="collapsed",
        )

    with send_col:
        submitted = st.form_submit_button(
            "Send",
            use_container_width=True,
            disabled=st.session_state.is_sending,
        )

st.markdown("</div></div>", unsafe_allow_html=True)


# -----------------------------
# Handle submit
# -----------------------------
if submitted:
    process_prompt(prompt)
    st.rerun()
