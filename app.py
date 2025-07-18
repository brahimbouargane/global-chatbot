import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - Centralized settings
class Config:
    PROJECT_NAME = "AI PDF Assistant"
    COMPANY_NAME = "Powered by AI"
    PDF_FILE_PATH = "data/reforming-modernity.pdf"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    MAX_CONTENT_LENGTH = 12000
    PREVIEW_LENGTH = 800

# Initialize OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# Page configuration with better metadata
st.set_page_config(
    page_title=Config.PROJECT_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': f"# {Config.PROJECT_NAME}\nChat with your PDF documents using AI"
    }
)

# Enhanced CSS with modern design and accessibility
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-color: #1f2937;
        --secondary-color: #3b82f6;
        --success-color: #10b981;
        --error-color: #ef4444;
        --warning-color: #f59e0b;
        --background-light: #f8fafc;
        --background-dark: #ffffff;
        --text-primary: #111827;
        --text-secondary: #6b7280;
        --border-color: #e5e7eb;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Global font */
    .main, .sidebar .sidebar-content {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, var(--secondary-color), #8b5cf6);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: var(--shadow-lg);
    }
    
    .main-header h1 {
        margin: 0 0 0.5rem 0;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Chat message containers */
    .chat-message {
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid var(--border-color);
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }
    
    .user-message {
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        border-left: 4px solid var(--secondary-color);
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-left: 4px solid var(--success-color);
        margin-right: 2rem;
    }
    
    .message-header {
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.95rem;
    }
    
    .message-content {
        color: var(--text-primary);
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background: var(--background-light);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }
    
    .info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }
    
    .info-item:last-child {
        border-bottom: none;
    }
    
    .info-label {
        font-weight: 500;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    .info-value {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.9rem;
    }
    
    /* Status indicators */
    .status-success {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-flex;
        gap: 0.25rem;
        align-items: center;
    }
    
    .loading-dots::after {
        content: '';
        width: 6px;
        height: 6px;
        background: var(--secondary-color);
        border-radius: 50%;
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0%, 20%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-secondary);
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary-color), #1d4ed8);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: var(--shadow);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid var(--border-color);
        transition: border-color 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .chat-message {
            margin-left: 0.5rem;
            margin-right: 0.5rem;
            padding: 1rem;
        }
        
        .user-message {
            margin-left: 0;
        }
        
        .assistant-message {
            margin-right: 0;
        }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state() -> None:
    """Initialize session state variables with proper typing"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'pdf_content' not in st.session_state:
        st.session_state.pdf_content = None
    if 'pdf_loaded' not in st.session_state:
        st.session_state.pdf_loaded = False
    if 'pdf_metadata' not in st.session_state:
        st.session_state.pdf_metadata = {}

@st.cache_data(show_spinner=False)
def load_pdf() -> Tuple[Optional[str], str, Dict[str, Any]]:
    """
    Load PDF with comprehensive error handling and metadata extraction
    
    Returns:
        Tuple of (content, message, metadata)
    """
    pdf_path = Path(Config.PDF_FILE_PATH)
    
    if not pdf_path.exists():
        return None, f"📄 PDF file not found: {Config.PDF_FILE_PATH}", {}
    
    try:
        reader = PdfReader(Config.PDF_FILE_PATH)
        text = ""
        total_pages = len(reader.pages)
        
        # Extract metadata
        metadata = {
            'total_pages': total_pages,
            'file_size': pdf_path.stat().st_size,
            'file_name': pdf_path.name,
            'creation_time': pdf_path.stat().st_ctime
        }
        
        # Extract text with progress indication
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                continue
        
        if not text.strip():
            return None, "⚠️ No readable text found in PDF", metadata
        
        # Add text statistics to metadata
        words = text.split()
        metadata.update({
            'word_count': len(words),
            'character_count': len(text),
            'estimated_reading_time': max(1, len(words) // 200)  # ~200 words per minute
        })
        
        return text, f"✅ Successfully loaded {total_pages} pages", metadata
        
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return None, f"❌ Error reading PDF: {str(e)}", {}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_ai_response(question: str, pdf_content: str) -> str:
    """
    Generate AI response with enhanced error handling and context management
    
    Args:
        question: User's question
        pdf_content: PDF content for context
        
    Returns:
        AI response string
    """
    # Handle greetings with more natural responses
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    question_clean = question.lower().strip()
    
    if any(greeting in question_clean for greeting in greetings):
        return f"""👋 Hello! Welcome to **{Config.PROJECT_NAME}**!

I'm your AI assistant, ready to help you explore and understand your PDF document. Here's what I can do:

• **Answer specific questions** about the document content
• **Summarize sections** or the entire document
• **Find and explain key concepts** mentioned in the text
• **Help you navigate** through different topics

What would you like to know about your document?"""
    
    if not client:
        return "🔑 **OpenAI client not initialized.** Please check your API key."
    
    try:
        # Truncate content to fit within token limits
        content_excerpt = pdf_content[:Config.MAX_CONTENT_LENGTH]
        
        system_prompt = f"""You are an expert document analyst helping users understand their PDF content. 

DOCUMENT CONTENT:
{content_excerpt}

INSTRUCTIONS:
- Provide accurate, helpful responses based solely on the document content
- Use markdown formatting for better readability
- Include page references when possible (look for "--- Page X ---" markers)
- If information isn't in the document, clearly state that
- Be conversational but professional
- Use bullet points and formatting to make responses scannable
- Quote relevant sections when helpful

Remember: Only use information from the provided document content."""

        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        if "rate_limit" in str(e).lower():
            return "⚠️ **Rate limit reached.** Please wait a moment before asking another question."
        elif "authentication" in str(e).lower() or "api_key" in str(e).lower():
            return "🔑 **Authentication error.** Please check your OpenAI API key."
        elif "invalid" in str(e).lower():
            return f"❌ **Invalid request:** {str(e)}"
        else:
            logger.error(f"Error generating AI response: {e}")
            return f"❌ **Error generating response:** {str(e)}"

def render_sidebar() -> None:
    """Render enhanced sidebar with PDF information and controls"""
    with st.sidebar:
        st.markdown("### 📄 Document Information")
        
        # Load PDF if not already loaded
        if st.session_state.pdf_content is None:
            with st.spinner("🔄 Loading PDF..."):
                pdf_content, message, metadata = load_pdf()
                st.session_state.pdf_content = pdf_content
                st.session_state.pdf_loaded = pdf_content is not None
                st.session_state.pdf_metadata = metadata
        
        # Display PDF status and information
        if st.session_state.pdf_loaded:
            st.markdown("""
            <div class="status-success">
                ✅ Document loaded successfully
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Document statistics
            metadata = st.session_state.pdf_metadata
            
            st.markdown("""
            <div class="sidebar-info">
                <div class="info-item">
                    <span class="info-label">📄 File Name:</span>
                    <span class="info-value">{}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📊 Pages:</span>
                    <span class="info-value">{}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📝 Words:</span>
                    <span class="info-value">{:,}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">💾 File Size:</span>
                    <span class="info-value">{}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">⏱️ Reading Time:</span>
                    <span class="info-value">~{} min</span>
                </div>
            </div>
            """.format(
                metadata.get('file_name', 'Unknown'),
                metadata.get('total_pages', 0),
                metadata.get('word_count', 0),
                format_file_size(metadata.get('file_size', 0)),
                metadata.get('estimated_reading_time', 1)
            ), unsafe_allow_html=True)
            
            # Document preview
            with st.expander("📖 Document Preview", expanded=False):
                if st.session_state.pdf_content:
                    preview_text = st.session_state.pdf_content[:Config.PREVIEW_LENGTH]
                    st.text_area(
                        "First part of the document:",
                        value=preview_text + ("..." if len(st.session_state.pdf_content) > Config.PREVIEW_LENGTH else ""),
                        height=200,
                        disabled=True,
                        key="preview"
                    )
        else:
            st.markdown("""
            <div class="status-error">
                ❌ Failed to load document
            </div>
            """, unsafe_allow_html=True)
            
            if 'message' in locals():
                st.error(message)
            
            st.info(f"📁 Looking for: `{Config.PDF_FILE_PATH}`")
        
        st.markdown("---")
        
        # Controls
        st.markdown("### 🔧 Controls")
        
        # Clear chat button with confirmation
        if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Reload PDF button
        if st.button("🔄 Reload Document", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.session_state.pdf_content = None
            st.session_state.pdf_loaded = False
            st.session_state.pdf_metadata = {}
            st.rerun()

def render_chat_interface() -> None:
    """Render the main chat interface"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 {}</h1>
        <p>{}</p>
    </div>
    """.format(Config.PROJECT_NAME, Config.COMPANY_NAME), unsafe_allow_html=True)
    
    # Check prerequisites
    if not OPENAI_API_KEY:
        st.error("🔑 **OpenAI API key not found!**")
        st.info("Please add your OpenAI API key to the `.env` file:")
        st.code("OPENAI_API_KEY=sk-your-api-key-here")
        st.stop()
    
    if not st.session_state.pdf_loaded:
        st.error("📄 **Document not loaded.** Please check the file path and try again.")
        return
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Empty state
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <h3>Ready to explore your document!</h3>
                <p>Ask me anything about the PDF content. I can help you:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Summarize key points</li>
                    <li>Find specific information</li>
                    <li>Explain complex concepts</li>
                    <li>Answer detailed questions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display chat messages
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <div class="message-header">
                            🙋 You
                        </div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <div class="message-header">
                            🤖 AI Assistant
                        </div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

def handle_user_input() -> None:
    """Handle user input and generate AI responses"""
    # Chat input
    if prompt := st.chat_input("💭 Ask me anything about your document..."):
        # Validate input
        if not prompt.strip():
            st.warning("⚠️ Please enter a question.")
            return
        
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": time.time()
        })
        
        # Generate AI response with loading indicator
        with st.spinner("🤔 Analyzing your question..."):
            response = get_ai_response(prompt, st.session_state.pdf_content)
        
        # Add AI response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": time.time()
        })
        
        # Rerun to update the interface
        st.rerun()

def main() -> None:
    """Main application function with proper error handling"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Render sidebar
        render_sidebar()
        
        # Render main chat interface
        render_chat_interface()
        
        # Handle user input
        handle_user_input()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"🚨 **Application Error:** {str(e)}")
        st.info("Please refresh the page and try again.")

if __name__ == '__main__':
    main()