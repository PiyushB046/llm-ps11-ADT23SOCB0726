"""
PS 11 - College Enquiry Chatbot

Answers questions about courses, fees and admissions using ONLY the
college info sheet (college_info.txt). The whole sheet is put into the
system prompt, and Google Gemini writes the answer.

Run:  streamlit run app.py      (put GEMINI_API_KEY in a .env file first)
"""

import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ============================================================
# 1. SETTINGS
# ============================================================
load_dotenv()  # loads GEMINI_API_KEY from the .env file

INFO_FILE = "college_info.txt"
MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]

# Buttons on the Ask page: (button text, question sent to the bot)
QUICK_QUESTIONS = [
    (":material/menu_book: Courses", "Which B.Tech branches are offered?"),
    (":material/payments: B.Tech fees", "What is the total B.Tech fee?"),
    (":material/description: Documents", "Which documents are needed for admission?"),
    (":material/apartment: Hostel", "Is there a hostel? What does it cost?"),
    (":material/verified: MBA eligibility", "What is the eligibility for MBA?"),
    (":material/work: Placements", "How are the placements?"),
]

# ============================================================
# 2. THE PROMPT
# ============================================================
PROMPT_RULES = """You are the admission enquiry assistant for a college.
Answer the user's question using ONLY the college information given below.

Rules:
1. If the answer is not in the information, reply exactly:
   "Sorry, I don't have that information. Please contact the admission office."
   and add the office phone/email from the info.
2. Never guess or invent fees, dates, seats or eligibility numbers.
3. Keep answers short (2-6 lines). Use bullet points for lists.
4. Mention amounts in Rupees exactly as written in the information.
5. Be polite. If the user greets you, greet back and say what you can help with.
"""


def build_system_prompt():
    """Rules + the full college info sheet = the system prompt."""
    with open(INFO_FILE, encoding="utf-8") as f:
        college_info = f.read()
    return PROMPT_RULES + "\nCOLLEGE INFORMATION:\n" + college_info


# ============================================================
# 3. TALKING TO GEMINI
# ============================================================
def ask_gemini(messages, model):
    """Send the chat so far to Gemini and return its reply."""
    # v1beta is needed for system instructions
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(api_version="v1beta"),
    )

    # Gemini calls the bot's role "model" instead of "assistant"
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(),
            temperature=0.2,  # low = factual, not creative
        ),
    )
    return response.text


def get_answer(model):
    """Ask Gemini using the last 10 messages; turn errors into a short message."""
    try:
        return ask_gemini(st.session_state.messages[-10:], model)
    except Exception as error:
        if "429" in str(error):  # 429 = free limit reached
            return "**The free Gemini limit has been reached.** Wait a minute, or pick another model in Settings."
        return f"**Something went wrong:** {error}"


# ============================================================
# 4. PAGES
# ============================================================
def show_navbar():
    """Top bar: brand, page buttons and the settings (gear) button. Returns the chosen model."""
    brand, links, gear = st.columns([2.5, 4, 0.6], vertical_alignment="center")

    brand.markdown(
        '<div class="brand"><span class="logo">E</span>'
        '<span>Enquiry Desk<small>College admissions · PS 11</small></span></div>',
        unsafe_allow_html=True,
    )

    pages = ["Home", "Ask", "How it works"]
    for column, name in zip(links.columns(3), pages):
        is_current = st.session_state.page == name
        if column.button(name, type="primary" if is_current else "tertiary", width="stretch"):
            st.session_state.page = name
            st.rerun()

    with gear.popover("", icon=":material/settings:"):
        st.markdown("#### Settings")
        model = st.selectbox("Gemini model", MODELS)
        st.caption("Each model has its own free daily limit.")
        if st.button("Clear chat", icon=":material/delete_sweep:", width="stretch"):
            st.session_state.messages = []
            st.rerun()
    return model


def show_home_page():
    st.markdown(
        """
        <div class="hero">
          <p class="eyebrow">Admissions 2026–27</p>
          <h1>Ask once.<br><span class="highlight">Answered instantly.</span></h1>
          <p class="intro">Courses, fees, eligibility and admissions, answered from the
          college's official info sheet. No queues. No guessing.</p>
        </div>
        <div class="stats">
          <div class="stat"><b>9</b><span>Programmes</span></div>
          <div class="stat"><b>600+</b><span>B.Tech seats</span></div>
          <div class="stat"><b>86%</b><span>Placement rate</span></div>
          <div class="stat"><b>28 LPA</b><span>Highest package</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start asking", icon=":material/arrow_forward:", type="primary"):
        st.session_state.page = "Ask"
        st.rerun()


def show_ask_page(model):
    st.markdown(
        '<p class="eyebrow">Ask the enquiry desk</p>'
        "<h2>Your enquiry. <span class='grey'>Our answers.</span></h2>",
        unsafe_allow_html=True,
    )

    # Quick-question buttons: clicking one asks that question
    question = None
    for column, (label, text) in zip(st.columns(6), QUICK_QUESTIONS):
        if column.button(label, width="stretch"):
            question = text

    # Show the chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # A typed question also counts
    typed = st.chat_input("Ask about courses, fees, admissions…")
    if typed:
        question = typed

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Checking the college info sheet…"):
                answer = get_answer(model)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    if not st.session_state.messages:
        st.info("No questions yet. Tap a topic above or type your own below.")


def show_how_page():
    st.markdown(
        """
        <p class="eyebrow">How it works</p>
        <h2>Three steps. <span class="grey">No guesswork.</span></h2>
        <div class="steps">
          <div class="step"><b>01</b><h3>The info sheet</h3>
            <p>Courses, fees, eligibility and dates are in one text file, college_info.txt.</p></div>
          <div class="step"><b>02</b><h3>A strict prompt</h3>
            <p>The whole sheet goes into the system prompt with one rule: answer only from it.</p></div>
          <div class="step"><b>03</b><h3>Gemini answers</h3>
            <p>Gemini replies in a few lines and remembers the last 10 messages.</p></div>
        </div>
        <div class="trust">
          <h3>Answers you can trust.</h3>
          <p>If the answer isn't in the sheet, the bot says so and gives the office's phone and email.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5. MAIN: runs from top to bottom on every click
# ============================================================
st.set_page_config(page_title="College Enquiry Chatbot", page_icon=":material/school:", layout="centered")

with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# session_state survives reruns, so the chat and current page are remembered
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "Home"

chosen_model = show_navbar()

if st.session_state.page == "Home":
    show_home_page()
elif st.session_state.page == "Ask":
    show_ask_page(chosen_model)
else:
    show_how_page()
