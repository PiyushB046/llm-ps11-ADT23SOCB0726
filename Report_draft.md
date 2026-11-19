# College Enquiry Chatbot: Procedure Report

**PS No:** 11 &nbsp;|&nbsp; **Name:** Piyush Bavane &nbsp;|&nbsp; **Roll No:** 11 (ADT23SOCB0726) &nbsp;|&nbsp; **Class:** BTech CSE
**GitHub:** https://github.com/PiyushB046/llm-ps11-ADT23SOCB0726

## 1. Problem statement
College admission offices get the same questions every day about courses, fees, eligibility and the admission process. This chatbot answers them instantly from the college's own information sheet, so students and parents get answers at any hour and admission staff save time.

## 2. Tools & model
**Language:** Python 3 · **LLM:** Google Gemini 3.5 Flash via the free Gemini API (`google-genai`); Llama 3.2 via Ollama as an offline option · **UI:** Streamlit (`st.chat_input`, `st.chat_message`, `st.session_state`, `st.popover`) with custom CSS · **Other:** python-dotenv, requests, Git/GitHub.

## 3. Procedure
1. Created a project folder and a virtual environment; installed streamlit, google-genai, python-dotenv and requests.
2. Got a free API key from Google AI Studio and saved it in `.env`, which is listed in `.gitignore` so it is never uploaded.
3. Wrote `college_info.txt` (sample data for a demo college) with courses, seats, fees, eligibility, admission steps, documents, dates, placements and facilities.
4. Designed the system prompt: the whole info sheet plus rules to answer only from it, never invent numbers, give a fixed fallback reply with contact details, and keep answers short.
5. Wrote `app.py`: it reads the info file, builds the system prompt, sends it with the last 10 chat messages to Gemini (temperature 0.2) and shows the reply.
6. Built the UI with three pages (Home, Ask, How it works) switched from a top navigation bar. The Ask page has six quick-question buttons and the chat; history is kept in `st.session_state.messages` so follow-up questions work. A settings button (top right) holds the model choice and "Clear chat". Custom CSS in `style.css` is added with `st.markdown(..., unsafe_allow_html=True)`.
7. Tested the app with the six questions below and took screenshots.
8. Wrote the README and requirements.txt and pushed the code to GitHub.

## 4. Prompt used
```
You are the admission enquiry assistant for a college.
Answer the user's question using ONLY the college information given below.
Rules:
1. If the answer is not in the information, reply exactly: "Sorry, I don't have that information.
   Please contact the admission office." and add the office phone/email.
2. Never guess or invent fees, dates, seats or eligibility numbers.
3. Keep answers short (2-6 lines). Use bullet points for lists.
4. Mention amounts in Rupees exactly as written in the information.
5. Be polite. If the user greets you, greet back and say what you can help with.
COLLEGE INFORMATION: """ <contents of college_info.txt> """
```
**Improvement made:** "answer from this info" alone does not say what to do when the answer is missing, which is where a model is most likely to guess. Rule 1 gives an exact fallback reply with the office contact, rule 2 forbids invented numbers, and the temperature was set low (0.2) for consistent answers. Test 6 below confirms the fallback works.

## 5. Results
| # | Input | Result |
|---|---|---|
| 1 | What B.Tech branches do you offer? | Listed all 6 branches ✔ |
| 2 | What is the total fee for B.Tech? | Rs. 1,60,000 = 1,45,000 tuition + 15,000 development ✔ |
| 3 | Which documents are needed for admission? | Full list of 9 documents ✔ |
| 4 | Is there a hostel and what does it cost? | Rs. 90,000 per year with mess ✔ |
| 5 | And can I pay that in instalments? (follow-up) | Used chat history: two instalments, July and December ✔ |
| 6 | What was last year's cut-off percentile? (not in sheet) | Fallback reply with office phone and email ✔ |

![](screenshots/3_chat_fees_hostel.png)

## 6. Challenges
- **400 "Developer instruction is not enabled for api version v1":** the system prompt needs the `v1beta` API, so the client is created with `HttpOptions(api_version="v1beta")`.
- **Chat history lost on every message**, because Streamlit reruns the script; fixed by storing messages in `st.session_state`.
- **429 RESOURCE_EXHAUSTED:** testing used up the free limit (per minute, then 20 requests/day on gemini-2.5-flash). Switched the default to gemini-3.5-flash, added a model picker in Settings and a friendly message when the limit is hit.
- **Role names:** Gemini uses `model` instead of `assistant`, so roles are converted before each call.

## 7. Conclusion
The chatbot answers course, fee and admission questions correctly from the info sheet, handles follow-up questions, and says so when it does not know. The info sheet holds sample data; it can be replaced with any college's real details without changing the code. A limitation is that the whole sheet is sent with every question, which will not scale to long brochures. **Future improvement:** retrieval (RAG with FAISS/ChromaDB) over the college's brochure PDF, and deployment on Streamlit Community Cloud.
