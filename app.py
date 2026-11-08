import streamlit as st
from openai import OpenAI
import pdfplumber
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
    if st.button("Restart New Session"):
        st.session_state.clear()
        st.rerun()

# --- Helper Functions ---
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
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
    system_prompt = f"""You are a strict examiner for {level} board exams. 
    You must generate questions based ONLY on the provided text.
    STRICT FORMATTING RULES:
    1. Each question must be on a NEW LINE.
    2. Do NOT use numbering (1., 2., etc.).
    3. Do NOT write 'Question:' or 'Answer:'.
    4. Only provide the question text.
    5. Provide exactly 5 questions.
    6. Do not combine multiple concepts into one question."""
    
    user_prompt = f"Extract 5 distinct questions from this textbook content:\n\n{text}"
    return get_ai_response(system_prompt, user_prompt)

def check_answer(question, student_answer, textbook_text, lang):
    # We pass the specific question as the main focus to prevent "mixing"
    system_prompt = f"You are a professional teacher. Verify the answer using ONLY the textbook context. Explain in {lang}."
    user_prompt = f"""
    TARGET QUESTION: {question}
    STUDENT'S ANSWER: {student_answer}
    TEXTBOOK CONTEXT: {textbook_text}
    
    Task: 
    - Compare the student's answer specifically against the target question.
    - State if it is correct, partially correct, or wrong.
    - Provide the accurate answer found in the textbook.
    - Explain the concept in {lang}.
    """
    return get_ai_response(system_prompt, user_prompt)

# --- Main Application Logic ---
if "textbook_text" not in st.session_state: st.session_state.textbook_text = ""
if "questions_list" not in st.session_state: st.session_state.questions_list = []

uploaded_file = st.file_uploader("Upload Chapter PDF", type="pdf")
if uploaded_file is not None and st.button("Process Chapter"):
    with st.spinner("Reading..."):
        text = extract_text_from_pdf(uploaded_file)
        if text.strip():
            st.session_state.textbook_text = text
            st.success("Textbook processed!")
        else:
            st.error("PDF is empty or a scanned image.")

if st.session_state.textbook_text:
    if st.button("Generate Practice Quiz"):
        with st.spinner("Extracting questions..."):
            raw_text = generate_questions(st.session_state.textbook_text, level)
            # Split by line and remove empty lines
            st.session_state.questions_list = [line.strip() for line in raw_text.split('\n') if line.strip()]
            st.success(f"Found {len(st.session_state.questions_list)} questions!")

# --- QUIZ INTERFACE ---
if st.session_state.questions_list:
    st.divider()
    st.markdown("### ✍️ Your Test Paper")
    
    for i, q in enumerate(st.session_state.questions_list):
        # Use a unique container for each question to prevent UI mixing
        with st.container():
            st.markdown(f"**Q{i+1}: {q}**")
            user_ans = st.text_area(f"Answer {i+1}", key=f"ans_{i}", label_visibility="collapsed", placeholder="Type your answer here...")
            
            if st.button(f"Verify Answer {i+1}", key=f"btn_{i}"):
                if user_ans:
                    with st.spinner("Verifying..."):
                        # We send the specific question 'q' to ensure the AI doesn't mix it up
                        feedback = check_answer(q, user_ans, st.session_state.textbook_text, language)
                        st.info(feedback)
                else:
                    st.warning("Please enter an answer first!")
            st.markdown("---")
