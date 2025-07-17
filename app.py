import streamlit as st
import openai
from PyPDF2 import PdfReader
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CUSTOMIZE THIS SECTION
PROJECT_NAME = "My PDF Chatbot"
COMPANY_NAME = "Your Company"
PDF_FILE_PATH = "data/reforming-modernity.pdf"

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Page configuration
st.set_page_config(page_title=PROJECT_NAME, page_icon="🤖", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
              color : #000;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color : #000;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        text : #000;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
            text : #000;
    }
    .pdf-info {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007acc;
            text : #000;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'pdf_content' not in st.session_state:
    st.session_state.pdf_content = None
if 'pdf_loaded' not in st.session_state:
    st.session_state.pdf_loaded = False

@st.cache_data
def load_pdf():
    """Load PDF from project with better error handling"""
    pdf_path = Path(PDF_FILE_PATH)
    
    if not pdf_path.exists():
        return None, f"PDF file not found: {PDF_FILE_PATH}"
    
    try:
        reader = PdfReader(PDF_FILE_PATH)
        text = ""
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text.strip():  # Only add non-empty pages
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
        
        return text, f"Successfully loaded {total_pages} pages"
    except Exception as e:
        return None, f"Error reading PDF: {str(e)}"

def get_pdf_info(pdf_content):
    """Get basic info about the PDF"""
    if not pdf_content:
        return {}
    
    lines = pdf_content.split('\n')
    pages = pdf_content.count('--- Page')
    words = len(pdf_content.split())
    characters = len(pdf_content)
    
    return {
        'pages': pages,
        'lines': len(lines),
        'words': words,
        'characters': characters
    }

def get_ai_response(question, pdf_content):
    """Generate response using OpenAI API"""
    simple_greetings = ['hello', 'hi', 'hey']
    question_clean = question.lower().strip()
    
    if question_clean in simple_greetings:
        return f"Hello! 👋 Welcome to {PROJECT_NAME}. Ask me anything about your PDF!"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Answer questions about this PDF: {pdf_content[:10000]}"},
                {"role": "user", "content": question}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.title(f"📄 {PROJECT_NAME}")
    st.markdown(f"*Powered by {COMPANY_NAME}*")
    
    # Check if API key is available
    if not OPENAI_API_KEY:
        st.error("❌ OpenAI API key not found!")
        st.info("Please add your OpenAI API key to the `.env` file:")
        st.code("OPENAI_API_KEY=sk-your-api-key-here")
        st.stop()
    
    # Sidebar for PDF info
    with st.sidebar:
        st.header("📄 Document Info")
        
        # Load PDF
        if st.session_state.pdf_content is None:
            with st.spinner("Loading PDF..."):
                pdf_content, message = load_pdf()
                st.session_state.pdf_content = pdf_content
                st.session_state.pdf_loaded = pdf_content is not None
        
        if st.session_state.pdf_loaded:
            st.success("✅ PDF loaded successfully!")
            
            # Show PDF info
            pdf_info = get_pdf_info(st.session_state.pdf_content)
            st.markdown(f"""
            **File:** `{Path(PDF_FILE_PATH).name}`  
            **Pages:** {pdf_info['pages']}  
            **Words:** {pdf_info['words']:,}  
            **Characters:** {pdf_info['characters']:,}
            """)
            
            # PDF Preview
            with st.expander("📖 Document Preview"):
                preview_text = st.session_state.pdf_content[:1000]
                st.text_area(
                    "First 1000 characters",
                    preview_text + "..." if len(st.session_state.pdf_content) > 1000 else preview_text,
                    height=200,
                    disabled=True
                )
        else:
            st.error("❌ Failed to load PDF")
            if 'message' in locals():
                st.error(message)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    if not st.session_state.pdf_loaded:
        st.error("Please check that your PDF file exists at the specified path and try again.")
        st.info(f"Looking for: `{PDF_FILE_PATH}`")
        return
    
    # Chat container
    st.markdown("### 💬 Chat with your PDF")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header">🙋 You</div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-header">🤖 Assistant</div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your PDF document..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate and add AI response
        with st.spinner("Analyzing document..."):
            response = get_ai_response(prompt, st.session_state.pdf_content)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to update chat
        st.rerun()

if __name__ == '__main__':
    main()