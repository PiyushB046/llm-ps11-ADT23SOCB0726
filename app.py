"""
PS 11 - College Enquiry Chatbot
Answers questions about courses, fees and admissions using ONLY the
college info sheet (college_info.txt), which is placed in the system prompt.

Run:  streamlit run app.py
LLM:  Google Gemini (free API key, set GEMINI_API_KEY in .env)
      or a local model through Ollama (no key needed).
"""

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from .env if present

INFO_FILE = Path(__file__).parent / "college_info.txt"
GEMINI_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]  # each has its own free quota
OLLAMA_URL = "http://localhost:11434/api/chat"
FALLBACK = "Sorry, I don't have that information. Please contact the admission office."

SYSTEM_PROMPT_TEMPLATE = """You are the admission enquiry assistant for a college.
Answer the user's question using ONLY the college information given below.

Rules:
1. If the answer is not in the information, reply exactly:
   "{fallback}" and add the office phone/email from the info.
2. Never guess or invent fees, dates, seats or eligibility numbers.
3. Keep answers short (2-6 lines). Use bullet points for lists.
4. Mention amounts in Rupees exactly as written in the information.
5. Be polite. If the user greets you, greet back and say what you can help with.

COLLEGE INFORMATION:
\"\"\"
{info}
\"\"\"
"""


def build_system_prompt() -> str:
    info = INFO_FILE.read_text(encoding="utf-8")
    return SYSTEM_PROMPT_TEMPLATE.format(info=info, fallback=FALLBACK)


def ask_gemini(system_prompt: str, history: list[dict], model: str) -> str:
    from google import genai
    from google.genai import types

    # system_instruction needs the v1beta API version
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    # Gemini uses roles "user" and "model"
    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in history
    ]
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.2),
    )
    return resp.text


def ask_ollama(system_prompt: str, history: list[dict], model: str) -> str:
    messages = [{"role": "system", "content": system_prompt}] + history
    r = requests.post(
        OLLAMA_URL,
        json={"model": model, "messages": messages, "stream": False, "options": {"temperature": 0.2}},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


# ---------------- UI ----------------
st.set_page_config(page_title="College Enquiry Chatbot", page_icon=":material/school:", layout="centered")

# Custom look: CSS from style.css + three floating background blobs
CSS = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
st.markdown('<div class="bg-fx"><div class="blob b1"></div><div class="blob b2"></div>'
            '<div class="blob b3"></div></div><div class="progress"></div>', unsafe_allow_html=True)

# Simple line icons (inline SVG) used in the HTML parts of the page
_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
ICON_CAP = _SVG.format('<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c3 2.5 9 2.5 12 0v-5"/><path d="M22 9v6"/>')
ICON_CHAT = _SVG.format('<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>')
ICON_HEART = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7.5-4.6-9.5-9.3C1 8 3.4 4.5 7 4.5c2 0 3.4 1.1 5 3 1.6-1.9 3-3 5-3 3.6 0 6 3.5 4.5 7.2C19.5 16.4 12 21 12 21z"/></svg>'
ICON_CHECK = _SVG.format('<path d="M5 12.5l4.5 4.5L19 7.5"/>')
ICON_SHIELD = _SVG.format('<path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>')
ICON_DOC = _SVG.format('<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5M8.5 13h7M8.5 17h5"/>')
ICON_SPARK = _SVG.format('<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>')

QUICK_QUESTIONS = [  # (button label, full question sent to the bot)
    (":material/menu_book: Courses", "Which B.Tech branches are offered?"),
    (":material/payments: B.Tech fees", "What is the total B.Tech fee?"),
    (":material/description: Documents", "Which documents are needed for admission?"),
    (":material/apartment: Hostel", "Is there a hostel? What does it cost?"),
    (":material/verified: MBA eligibility", "What is the eligibility for MBA?"),
    (":material/work: Placements", "How are the placements?"),
]
PAGES = {"home": "Home", "ask": "Ask", "how": "How it works"}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None
if "page" not in st.session_state:
    st.session_state.page = "home"


def go(page: str, question: str | None = None):
    """Switch page (and optionally queue a question to ask on the Ask page)."""
    st.session_state.page = page
    if question:
        st.session_state.pending = question


# ---------- top nav bar: brand | page links | status | settings ----------
c_brand, c_links, c_pill, c_gear = st.columns([2.3, 3.2, 2.2, 0.6], vertical_alignment="center")
with c_gear:
    with st.popover("", icon=":material/settings:", help="Settings"):
        st.markdown("#### Settings")
        provider = st.radio("LLM provider", ["Gemini", "Ollama (local)"])
        gemini_model = st.selectbox("Gemini model", GEMINI_MODELS) if provider == "Gemini" else None
        ollama_model = st.text_input("Ollama model", "llama3.2") if provider.startswith("Ollama") else None
        if provider == "Gemini" and not os.getenv("GEMINI_API_KEY"):
            st.warning("GEMINI_API_KEY not found. Add it to a .env file.")
        st.caption("Answers come only from `college_info.txt`. "
                   "Edit that file to use the bot for another college.")
        if st.button("Clear chat", icon=":material/delete_sweep:", width="stretch"):
            st.session_state.messages = []
            st.rerun()
model_label = gemini_model if provider == "Gemini" else ollama_model

c_brand.markdown(f"""<div class="brand"><span class="mark">{ICON_CAP}</span>
<span class="brand-name">Enquiry Desk<small>College admissions · PS 11</small></span></div>""",
                 unsafe_allow_html=True)
with c_links:
    st.markdown('<span class="navlinks"></span>', unsafe_allow_html=True)  # CSS marker
    link_cols = st.columns(len(PAGES), gap="small")
    for col, (key, label) in zip(link_cols, PAGES.items()):
        col.button(label, key=f"nav_{key}", on_click=go, args=(key,),
                   type="primary" if st.session_state.page == key else "tertiary", width="stretch")
c_pill.markdown(f'<div class="pill-wrap"><span class="pill"><span class="live"></span>'
                f'<span class="mono">online · {model_label}</span></span></div>', unsafe_allow_html=True)

page = st.session_state.page

# ---------- page: Home ----------
if page == "home":
    st.markdown(f"""
<div class="hero">
  <p class="eyebrow">Admissions 2026–27</p>
  <h1>Ask once.<br><span class="hl"><span class="grad-ink">Answered instantly.</span></span></h1>
  <p class="lede">Courses, fees, eligibility and admissions, answered from the college's
  official info sheet. No queues. No guessing.</p>
  <div class="checks">
    <span><i>{ICON_CHECK}</i>Open 24×7</span>
    <span><i>{ICON_CHECK}</i>Only official college data</span>
    <span><i>{ICON_CHECK}</i>Remembers follow-ups</span>
  </div>
</div>""", unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.3, 1.3, 3])
    b1.button("Start asking", icon=":material/arrow_forward:", type="primary", width="stretch",
              on_click=go, args=("ask",), key="cta_ask")
    b2.button("How it works", width="stretch", on_click=go, args=("how",), key="cta_how")
    st.markdown("""
<div class="stats">
  <div class="stat"><b>9</b><span>Programmes</span></div>
  <div class="stat"><b>600+</b><span>B.Tech seats</span></div>
  <div class="stat"><b>86%</b><span>Placement rate</span></div>
  <div class="stat"><b>28 LPA</b><span>Highest package</span></div>
</div>""", unsafe_allow_html=True)

# ---------- page: Ask (chat) ----------
elif page == "ask":
    st.markdown('<div class="sec top"><p class="eyebrow">Ask the enquiry desk</p>'
                '<h2>Your enquiry. <span class="muted-ink">Our answers.</span></h2></div>',
                unsafe_allow_html=True)
    qcols = st.columns(6)
    for col, (label, q) in zip(qcols, QUICK_QUESTIONS):
        col.button(label, key=q, help=q, width="stretch", on_click=go, args=("ask", q))

    if not st.session_state.messages and not st.session_state.pending:
        st.markdown('<div class="empty"><div class="empty-icon">' + ICON_CHAT + '</div><p>No questions yet. '
                    'Tap a topic above or type your own below.</p></div>', unsafe_allow_html=True)

    AVATARS = {"user": ":material/person:", "assistant": ":material/school:"}
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
            if msg["role"] == "user":
                st.markdown('<span class="u-msg"></span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

    typed = st.chat_input("Ask about courses, fees, admissions…")
    question = typed or st.session_state.pending
    st.session_state.pending = None

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user", avatar=AVATARS["user"]):
            st.markdown('<span class="u-msg"></span>', unsafe_allow_html=True)
            st.markdown(question)

        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            with st.spinner("Checking the college info sheet…"):
                try:
                    system_prompt = build_system_prompt()
                    history = st.session_state.messages[-10:]  # last 10 turns keeps the prompt small
                    if provider == "Gemini":
                        answer = ask_gemini(system_prompt, history, gemini_model)
                    else:
                        answer = ask_ollama(system_prompt, history, ollama_model)
                except Exception as e:
                    if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                        answer = ("**The free Gemini limit has been reached.** Wait a minute and try again, "
                                  "or pick another Gemini model in Settings (top right).")
                    else:
                        answer = f"**Error contacting the LLM:** {str(e)[:200]}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

# ---------- page: How it works ----------
else:
    st.markdown(f"""
<div class="sec top"><p class="eyebrow">How it works</p>
<h2>Three steps. <span class="muted-ink">No guesswork.</span></h2></div>
<div class="steps">
  <div class="step"><span class="step-icon">{ICON_DOC}<b class="num">01</b></span>
    <h3>The info sheet</h3><p>Courses, fees, eligibility and dates live in one plain text file, <code>college_info.txt</code>.</p></div>
  <div class="step"><span class="step-icon">{ICON_SPARK}<b class="num">02</b></span>
    <h3>A strict prompt</h3><p>The whole sheet goes into the system prompt with one rule: answer only from this information.</p></div>
  <div class="step"><span class="step-icon">{ICON_CHAT}<b class="num">03</b></span>
    <h3>Gemini answers</h3><p>Gemini replies in a few lines and remembers the last ten messages for follow-ups.</p></div>
</div>
<div class="cta"><span class="cta-icon">{ICON_SHIELD}</span><div><p class="eyebrow">No guessing</p>
<h3>Answers you can trust.</h3>
<p>If the answer isn't in the sheet, the bot says so and gives the admission office's phone and email.</p></div></div>
<div class="foot"><span>Made with <span class="heart">{ICON_HEART}</span> for the LLM Mini Project · PS 11</span>
<span class="mono">streamlit · gemini</span></div>
""", unsafe_allow_html=True)
    st.button("Try it now", icon=":material/arrow_forward:", type="primary", on_click=go, args=("ask",), key="cta_try")
