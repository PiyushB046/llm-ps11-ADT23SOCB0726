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
MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]  # first = default

# Buttons on the Ask page: (button text, question sent to the bot)
QUICK_QUESTIONS = [
    (":material/menu_book: Courses", "Which B.Tech branches are offered?"),
    (":material/payments: B.Tech fees", "What is the total B.Tech fee?"),
    (":material/description: Documents", "Which documents are needed for admission?"),
    (":material/apartment: Hostel", "Is there a hostel? What does it cost?"),
    (":material/verified: MBA eligibility", "What is the eligibility for MBA?"),
    (":material/work: Placements", "How are the placements?"),
]

# Programme facts shown on the Home page (copied from college_info.txt)
PROGRAMMES = {
    "B.Tech": {"fee": "1.6L", "full_fee": "Rs 1,60,000", "years": "4 years", "seats": "600 seats", "exam": "MHT-CET / JEE"},
    "MBA": {"fee": "1.25L", "full_fee": "Rs 1,25,000", "years": "2 years", "seats": "60 seats", "exam": "CAT / CMAT"},
    "MCA": {"fee": "95K", "full_fee": "Rs 95,000", "years": "2 years", "seats": "60 seats", "exam": "MAH-MCA-CET"},
    "M.Tech": {"fee": "1.1L", "full_fee": "Rs 1,10,000", "years": "2 years", "seats": "24 seats", "exam": "GATE"},
}

# Facts that scroll along the bottom of the Home page
TICKER = ["86% placed in 2025-26", "Highest package 28 LPA", "Hostel with mess Rs 90,000 a year",
          "NAAC A grade", "Fees in two instalments", "Classes begin 1 August 2026", "Merit scholarship up to 25%"]

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
    """Ask Gemini using the last 10 messages.
    If the chosen model's free limit is used up (error 429), try the other models one by one."""
    models_to_try = [model] + [m for m in MODELS if m != model]
    for m in models_to_try:
        try:
            return ask_gemini(st.session_state.messages[-10:], m)
        except Exception as error:
            if "429" in str(error):  # 429 = free limit reached, so try the next model
                continue
            return f"**Something went wrong:** {error}"
    return ("**The free Gemini limit is used up on every model.** "
            "It resets at 1:30 PM India time (midnight in California).")


# ============================================================
# 4. PAGES
# ============================================================
def go_to(page):
    """Switch to another page and redraw the screen."""
    st.session_state.page = page
    st.rerun()


def show_navbar():
    """Top bar: brand + numbered page buttons, a 'Start asking' button and the gear. Returns the model."""
    bar, cta, gear = st.columns([5, 1.6, 0.55], vertical_alignment="center")

    # The pink segmented bar (styled in style.css as .st-key-navbar)
    with bar.container(key="navbar", horizontal=True, gap=None, vertical_alignment="center"):
        st.markdown('<div class="brand">Enquiry Desk</div>', unsafe_allow_html=True)
        for number, name in enumerate(["Home", "Ask", "How it works"], start=1):
            is_current = st.session_state.page == name
            if st.button(f"{name} `0{number}`", type="primary" if is_current else "tertiary", width="stretch"):
                go_to(name)

    if cta.button("Start asking", icon=":material/arrow_forward:", icon_position="right",
                  type="primary", key="cta_top", width="stretch"):
        go_to("Ask")

    with gear.popover("", icon=":material/settings:"):
        st.markdown("#### Settings")
        model = st.selectbox("Gemini model", MODELS)
        st.caption("Each model has its own free daily limit.")
        if st.button("Clear chat", icon=":material/delete_sweep:", width="stretch"):
            st.session_state.messages = []
            st.rerun()
    return model


def show_home_page():
    """Headline on the left; on the right a 3D cube on a pink stage with two tickets, and programme chips."""
    if st.session_state.get("programme") not in PROGRAMMES:
        st.session_state.programme = "B.Tech"
    name = st.session_state.programme
    p = PROGRAMMES[name]

    text, stage = st.columns([1, 1.1], gap="large", vertical_alignment="center")

    with text:
        st.markdown(
            """
            <div class="eyebrow"><span class="dot"></span>Admissions 2026–27 · now open</div>
            <h1 class="headline">Admissions,<br><span class="mark">answered.</span></h1>
            <p class="lead">Courses, fees, eligibility, documents: ask the enquiry desk anything. Every answer comes
            straight from the college's official info sheet, so it never guesses.</p>
            """,
            unsafe_allow_html=True,
        )
        with st.container(horizontal=True, gap="small"):
            if st.button("Start asking", icon=":material/arrow_forward:", icon_position="right",
                         type="primary", key="home_ask"):
                go_to("Ask")
            if st.button("How it works", key="home_how"):
                go_to("How it works")
        st.markdown(
            """
            <div class="facts">
              <div><b>9</b><span>programmes</span></div>
              <div><b>86%</b><span>placed last year</span></div>
              <div><b>28 LPA</b><span>highest package</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with stage:
        st.markdown(
            f"""
            <div class="stage">
              <div class="ticket light tilt-left"><small>you ask</small><b>{name} fees?</b></div>
              <div class="scene"><div class="plate"></div>
                <div class="cube">
                  <div class="face front"><small>{p["years"]}</small><b>{name}</b><em>{p["exam"]}</em></div>
                  <div class="face side"><b>{p["seats"]}</b></div>
                  <div class="face top"></div>
                </div>
              </div>
              <div class="ticket dark tilt-right"><small>the answer · per year</small><b>Rs {p["fee"]}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Programme chips. The choice is saved in st.session_state.programme (key="programme").
        st.segmented_control("Programme", list(PROGRAMMES), key="programme", required=True,
                             label_visibility="collapsed", width="stretch")

    # Wine band with facts scrolling sideways (the list is repeated so the loop looks seamless)
    items = "".join(f"<span>{fact}</span>" for fact in TICKER * 2)
    st.markdown(f'<div class="ticker"><div class="track">{items}</div></div>', unsafe_allow_html=True)


def show_ask_page(model):
    """Topics on the left, the chat on the right."""
    topics, chat = st.columns([1, 2.6], gap="large")

    # Left: quick-question buttons. Clicking one asks that question.
    question = None
    with topics:
        st.markdown('<div class="eyebrow"><span class="dot"></span>Popular topics</div>', unsafe_allow_html=True)
        for label, text in QUICK_QUESTIONS:
            if st.button(label, width="stretch"):
                question = text
        st.markdown(
            '<div class="ticket light small"><small>good to know</small>'
            "<p>Answers come only from the college info sheet. If something isn't there, "
            "the desk gives you the office's phone and email.</p></div>",
            unsafe_allow_html=True,
        )

    # The chat box at the bottom of the screen
    typed = st.chat_input("Ask about courses, fees, admissions…")
    if typed:
        question = typed

    with chat:
        st.markdown('<h2 class="title">Your enquiry. <span class="soft">Our answers.</span></h2>',
                    unsafe_allow_html=True)

        # Show the chat history
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

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
            st.markdown(
                '<div class="empty"><div class="ticket dark"><small>start here</small><b>Ask away.</b></div>'
                "<p>Pick a popular topic or type your own question below.</p></div>",
                unsafe_allow_html=True,
            )


def show_how_page():
    """Three ticket steps joined by a dashed line, and a wine band."""
    st.markdown(
        """
        <div class="eyebrow"><span class="dot"></span>How it works</div>
        <h2 class="title big">Three steps.<br><span class="soft">No guesswork.</span></h2>
        <div class="steps">
          <div class="ticket light step"><small>step 01</small><b>The info sheet</b>
            <p>Courses, fees, eligibility and dates are kept in one text file, college_info.txt.</p></div>
          <div class="ticket light step"><small>step 02</small><b>A strict prompt</b>
            <p>The whole sheet goes into the system prompt with one rule: answer only from it.</p></div>
          <div class="ticket dark step"><small>step 03</small><b>Gemini answers</b>
            <p>A short, exact reply. The last 10 messages are sent too, so follow-ups work.</p></div>
        </div>
        <div class="band">
          <div><small>no guessing</small><h3>Answers you can trust.</h3></div>
          <p>If the answer isn't in the sheet, the desk says so and gives the admission office's phone and email.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Try it now", icon=":material/arrow_forward:", icon_position="right", type="primary", key="how_try"):
        go_to("Ask")


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
