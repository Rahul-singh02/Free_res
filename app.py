import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai

load_dotenv()

st.set_page_config(
    page_title="Exam Prep AI | Question Bank & Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    .stSidebar {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #58A6FF !important;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #2EA043;
        border: none;
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background-color: #161B22 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

def extract_text_from_pdfs(pdf_files) -> str:
    combined_text = ""
    for pdf_file in pdf_files:
        try:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    combined_text += text + "\n"
        except Exception as e:
            st.error(f"Error reading {pdf_file.name}: {e}")
    return combined_text

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("`GEMINI_API_KEY` is missing. Set it in Render Environment Variables.")
        st.stop()
    return genai.Client(api_key=api_key)

st.title("🎓 College Exam Prep AI Assistant")
st.caption("Upload Previous Year Questions (PYQs) and Syllabus to categorize topics or generate practice questions.")

with st.sidebar:
    st.header("📂 Document Uploads")
    
    syllabus_files = st.file_uploader(
        "Upload Syllabus (PDF)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="syllabus_uploader"
    )
    
    pyq_files = st.file_uploader(
        "Upload Previous Year Papers (PDF)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="pyq_uploader"
    )
    
    st.markdown("---")
    st.markdown("**Status:**")
    syllabus_text = extract_text_from_pdfs(syllabus_files) if syllabus_files else ""
    pyq_text = extract_text_from_pdfs(pyq_files) if pyq_files else ""
    
    if syllabus_text:
        st.success(f"✓ Syllabus loaded ({len(syllabus_text.split())} words)")
    if pyq_text:
        st.success(f"✓ PYQs loaded ({len(pyq_text.split())} words)")

tab1, tab2 = st.tabs(["🏷️ Topic-Wise Categorization", "🎯 Practice Question Generator"])

# Tab 1: Topic Categorization
with tab1:
    st.header("Topic-Wise PYQ Categorization")
    st.write("Extracts questions from your uploaded PYQs and groups them under syllabus topics.")

    if st.button("Categorize Questions", key="btn_categorize"):
        if not pyq_text or not syllabus_text:
            st.warning("Please upload both Syllabus and Previous Year Papers in the sidebar first.")
        else:
            with st.spinner("Analyzing documents and organizing questions..."):
                try:
                    client = get_gemini_client()
                    
                    prompt = f"""
                    You are an expert college academic counselor and exam analyzer.
                    Below is the content of a course Syllabus and Previous Year Question Papers (PYQs).

                    SYLLABUS CONTENT:
                    {syllabus_text[:10000]}

                    PREVIOUS YEAR QUESTIONS CONTENT:
                    {pyq_text[:15000]}

                    TASKS:
                    1. Read the syllabus to identify all major units/modules and sub-topics.
                    2. Extract all individual questions from the Previous Year Question Papers.
                    3. Group every extracted question under its relevant Syllabus Topic/Module.
                    4. Format the output cleanly using Markdown with clear heading titles for each topic and bullet points for questions.
                    """

                    # FIXED: Changed model name to gemini-1.5-flash
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=prompt,
                    )

                    st.markdown("### Categorized Questions")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Failed to generate output: {e}")

# Tab 2: Question Generation
with tab2:
    st.header("Generate Similar Practice Questions")
    st.write("Generates practice questions mirroring past paper patterns.")

    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.slider("Number of Questions", min_value=3, max_value=20, value=5)
    with col2:
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard", "Mixed Exam Standard"])

    target_topic = st.text_input("Specific Topic (Optional)", placeholder="e.g., Dynamic Programming, Thermodynamics")

    if st.button("Generate Extra Questions", key="btn_generate"):
        if not pyq_text or not syllabus_text:
            st.warning("Please upload both Syllabus and Previous Year Papers in the sidebar first.")
        else:
            with st.spinner("Generating practice questions..."):
                try:
                    client = get_gemini_client()
                    
                    topic_clause = f"Focus specifically on: '{target_topic}'." if target_topic else "Cover key topics across the syllabus."

                    prompt = f"""
                    You are an expert college exam parser and test creator.
                    
                    SYLLABUS CONTENT:
                    {syllabus_text[:10000]}

                    PAST YEAR EXAM PAPERS:
                    {pyq_text[:15000]}

                    TASK:
                    Generate exactly {num_questions} NEW, unique practice questions that mimic the structure and weightage of past year questions.
                    Difficulty level: {difficulty}.
                    {topic_clause}

                    REQUIREMENTS:
                    - Do NOT copy past questions directly.
                    - Format using Markdown numbered lists.
                    - State which syllabus unit each question tests.
                    - Add a 2-3 line answer outline/hint for each question.
                    """

                    # FIXED: Changed model name to gemini-1.5-flash
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=prompt,
                    )

                    st.markdown("### Generated Practice Paper")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"Failed to generate questions: {e}")