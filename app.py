import streamlit as st
from openai import OpenAI
import PyPDF2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- OpenRouter Configuration ---
# Initialize OpenAI client but point it to OpenRouter's URL
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# --- Page Configuration ---
st.set_page_config(page_title="Sabaq AI - Your Personal Tutor", page_icon="📖", layout="wide")

st.markdown('<p style="font-size:50px; font-weight:bold; color:#2E86C1; text-align:center;">📖 Sabaq AI</p>', unsafe_allow_html=True)
st.markdown('<p style="font-size:20px; text-align:center; color:#5D6D7E; margin-bottom:30px;">Your AI-powered textbook companion for Matric & Inter</p>', unsafe_allow_html=True)

# --- Sidebar Settings ---
with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Choose Explanation Language", ["English", "Urdu (اردو)", "Roman Urdu"])
    level = st.selectbox("Education Level", ["Matric (9th/10th)", "Intermediate (11th/12th)"])
    
    # Allow the user to change the model if they want
    model_choice = st.selectbox("AI Model", ["google/gemini-flash-1.5", "openai/gpt-4o-mini", "meta-llama/llama-3-8b-instruct"])
    st.info("Sabaq AI is now powered by OpenRouter!")

# --- Helper Functions ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_ai_response(system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model=model_choice, # Uses the model selected in sidebar
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "https://sabaq-ai.streamlit.app/", # Required by OpenRouter
                "X-Title": "Sabaq AI", # Required by OpenRouter
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_questions(text, level):
    system_prompt = f"You are an expert teacher for the Pakistani {level} board exams."
    user_prompt = f"Based on this text, create 3 MCQs and 2 Short Questions. Text: {text}"
    return get_ai_response(system_prompt, user_prompt)

def check_answer(question, student_answer, textbook_text, lang):
    system_prompt = f"You are a helpful Pakistani teacher. Explain clearly in {lang}."
    user_prompt = f"Question: {question}\nStudent Answer: {student_answer}\nContext: {textbook_text}\nTell if it's correct and explain why in {lang}."
    return get_ai_response(system_prompt, user_prompt)

# --- Main Application Logic ---
if "textbook_text" not in st.session_state: st.session_state.textbook_text = ""
if "questions" not in st.session_state: st.session_state.questions = ""

uploaded_file = st.file_uploader("Upload Chapter PDF", type="pdf")
if uploaded_file is not None and st.button("Process Chapter"):
    with st.spinner("Reading..."):
        st.session_state.textbook_text = extract_text_from_pdf(uploaded_file)
        st.success("Chapter uploaded!")

if st.session_state.textbook_text and st.button("Generate Practice Questions"):
    with st.spinner("Generating..."):
        st.session_state.questions = generate_questions(st.session_state.textbook_text, level)
        st.markdown("### 📝 Your Practice Test")
        st.write(st.session_state.questions)

if st.session_state.questions:
    st.divider()
    user_question = st.text_input("Paste the question:")
    user_answer = st.text_area("Type your answer:")
    if st.button("Check My Answer") and user_answer:
        with st.spinner("Evaluating..."):
            feedback = check_answer(user_question, user_answer, st.session_state.textbook_text, language)
            st.info(feedback)
