import streamlit as st
from openai import OpenAI
import PyPDF2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
# Ensure you have OPENAI_API_KEY in your .env file
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Page Configuration ---
st.set_page_config(
    page_title="Sabaq AI - Your Personal Tutor", 
    page_icon="📖", 
    layout="wide"
)

# Custom CSS for Branding
st.markdown("""
    <style>
    .main-title {
        font-size: 50px;
        font-weight: bold;
        color: #2E86C1;
        text-align: center;
    }
    .sub-title {
        font-size: 20px;
        text-align: center;
        color: #5D6D7E;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📖 Sabaq AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Your AI-powered textbook companion for Matric & Inter</p>', unsafe_allow_html=True)

# --- Sidebar Settings ---
with st.sidebar:
    st.header("Settings")
    language = st.selectbox(
        "Choose Explanation Language", 
        ["English", "Urdu (اردو)", "Roman Urdu"]
    )
    level = st.selectbox(
        "Education Level", 
        ["Matric (9th/10th)", "Intermediate (11th/12th)"]
    )
    st.info("Sabaq AI helps you prepare for board exams by generating questions from your own textbook.")

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
            model="gpt-4o-mini", # Fast and cost-effective
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_questions(text, level):
    system_prompt = f"You are an expert teacher for the Pakistani {level} board exams."
    user_prompt = f"""
    Based on the following textbook text, create a practice test.
    Include:
    1. 3 Multiple Choice Questions (MCQs) with options.
    2. 2 Short Questions.
    
    Textbook Content:
    {text}
    
    Format the output clearly. Provide the questions first, and keep the answers hidden at the very end.
    """
    return get_ai_response(system_prompt, user_prompt)

def check_answer(question, student_answer, textbook_text, lang):
    system_prompt = f"You are a helpful Pakistani teacher. You explain things clearly in {lang}."
    user_prompt = f"""
    Question: {question}
    Student's Answer: {student_answer}
    Correct Textbook Context: {textbook_text}
    
    Task:
    1. Tell the student if their answer is correct, partially correct, or wrong.
    2. Provide the correct answer based on the textbook.
    3. Explain the concept simply in {lang}.
    
    If the language is 'Roman Urdu', use Latin script (e.g., 'Aapka jawab sahi hai...').
    If the language is 'Urdu (اردو)', use Urdu script.
    """
    return get_ai_response(system_prompt, user_prompt)

# --- Main Application Logic ---

# Session state to store data
if "textbook_text" not in st.session_state:
    st.session_state.textbook_text = ""
if "questions" not in st.session_state:
    st.session_state.questions = ""

# 1. File Upload
uploaded_file = st.file_uploader("Upload Chapter PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Process Chapter"):
        with st.spinner("Reading your textbook..."):
            st.session_state.textbook_text = extract_text_from_pdf(uploaded_file)
            st.success("Chapter uploaded successfully!")

# 2. Question Generation
if st.session_state.textbook_text:
    if st.button("Generate Practice Questions"):
        with st.spinner("Creating your exam..."):
            st.session_state.questions = generate_questions(st.session_state.textbook_text, level)
            st.markdown("### 📝 Your Practice Test")
            st.write(st.session_state.questions)

# 3. Answer Checking
if st.session_state.questions:
    st.divider()
    st.markdown("### ✍️ Submit Your Answer")
    user_question = st.text_input("Paste the question you are answering:")
    user_answer = st.text_area("Type your answer here:")
    
    if st.button("Check My Answer"):
        if user_answer:
            with st.spinner("Evaluating..."):
                feedback = check_answer(user_question, user_answer, st.session_state.textbook_text, language)
                st.markdown("#### 🎓 Teacher's Feedback:")
                st.info(feedback)
        else:
            st.warning("Please type an answer first!")
