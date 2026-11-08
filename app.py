import streamlit as st
from openai import OpenAI
import PyPDF2
import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter Configuration ---
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
    model_choice = st.selectbox("AI Model", ["liquid/lfm-3-1.7b:free", "openai/gpt-4o-mini"])
    if st.button("Clear All Data"):
        st.session_state.textbook_text = ""
        st.session_state.questions_list = []
        st.rerun()

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
            model=model_choice,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers={"HTTP-Referer": "https://sabaq-ai.streamlit.app/", "X-Title": "Sabaq AI"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_questions(text, level):
    system_prompt = f"You are an expert teacher for Pakistani {level} board exams."
    user_prompt = f"""
    Based on the textbook text provided, create exactly 5 practice questions.
    
    CRITICAL INSTRUCTION: 
    Separate every single question with the symbol '###'. 
    Do not write 'Question 1' or 'Answer'. 
    Just write the question, then '###', then the next question.
    
    Example:
    What is photosynthesis? ### Define Gravity. ### What is the capital of Pakistan?
    
    Textbook Content:
    {text}
    """
    return get_ai_response(system_prompt, user_prompt)

def check_answer(question, student_answer, textbook_text, lang):
    system_prompt = f"You are a helpful Pakistani teacher. Explain clearly in {lang}."
    user_prompt = f"Question: {question}\nStudent Answer: {student_answer}\nContext: {textbook_text}\nTell if it's correct and explain why in {lang}."
    return get_ai_response(system_prompt, user_prompt)

# --- Main Application Logic ---
if "textbook_text" not in st.session_state: st.session_state.textbook_text = ""
if "questions_list" not in st.session_state: st.session_state.questions_list = []

uploaded_file = st.file_uploader("Upload Chapter PDF", type="pdf")
if uploaded_file is not None and st.button("Process Chapter"):
    with st.spinner("Reading..."):
        st.session_state.textbook_text = extract_text_from_pdf(uploaded_file)
        st.success("Chapter uploaded!")

if st.session_state.textbook_text:
    if st.button("Generate Practice Quiz"):
        with st.spinner("Finding all questions..."):
            raw_text = generate_questions(st.session_state.textbook_text, level)
            # Split by the special symbol '###'
            st.session_state.questions_list = [q.strip() for q in raw_text.split('###') if q.strip()]
            st.success(f"Found {len(st.session_state.questions_list)} questions!")

# --- QUIZ INTERFACE ---
if st.session_state.questions_list:
    st.divider()
    st.markdown("### ✍️ Your Personalized Test Paper")
    
    for i, q in enumerate(st.session_state.questions_list):
        # Using an expander to keep the UI clean
        with st.expander(f"Question {i+1}: {q[:60]}...", expanded=True):
            st.markdown(f"**{q}**")
            user_ans = st.text_area(f"Your answer for Q{i+1}", key=f"ans_{i}", label_visibility="collapsed")
            
            if st.button(f"Check Answer {i+1}", key=f"btn_{i}"):
                if user_ans:
                    with st.spinner("Evaluating..."):
                        feedback = check_answer(q, user_ans, st.session_state.textbook_text, language)
                        st.info(feedback)
                else:
                    st.warning("Please type your answer first!")
