# College Enquiry Chatbot (LLM Mini Project, PS 11)

## Problem statement
Admission offices answer the same questions again and again. This chatbot answers questions about
courses, fees, eligibility and admissions using **only** the college's info sheet (`college_info.txt`).

## How it works
1. The college info is stored in `college_info.txt`.
2. The info is put into the **system prompt** with the rule "answer only from this info". If the answer isn't there, the bot gives a fixed fallback reply.
3. The Streamlit chat UI uses `st.chat_input`, and the chat history is kept in `st.session_state`.
4. The look (colours, fonts, buttons, chat bubbles) comes from `style.css` and `.streamlit/config.toml`.
5. The LLM is **Gemini 3.5 Flash** (free API key). 3.5 Flash Lite and 2.5 Flash can be picked in Settings (gear icon, top right).

## How to run
```bash
pip install -r requirements.txt
cp .env.example .env        # then paste your Gemini API key into .env
streamlit run app.py
```

To use the bot for a different college, edit `college_info.txt`. You don't need to change any code.

## Screenshots
![Home](screenshots/1_home.png)
![Chat](screenshots/3_chat_fees_hostel.png)

## Tech stack
Python · Streamlit · Google Gemini API (google-genai) · python-dotenv
