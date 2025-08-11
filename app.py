import streamlit as st
from openai import OpenAI
import os
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any
import logging
import base64

try:
    from ethics_handler import render_ethics_chat_interface, initialize_ethics_session_state
    ETHICS_AVAILABLE = True
except ImportError as e:
    ETHICS_AVAILABLE = False

# Add PDF reading functionality
from PyPDF2 import PdfReader

# Import our localization system
from localization import language_manager, t, init_language_system, render_language_selector, get_rtl_css

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - Updated for multiple ethics PDFs
class Config:
    PROJECT_NAME = "Comprehensive Ethics Assistant"
    COMPANY_NAME = "Ethics Center"
    LOGO_PATH = "logo.png"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    TTS_MODEL = "tts-1"
    TTS_VOICE = "alloy"
    SUPPORTED_VOICES = {
        'alloy': 'Alloy (Neutral)',
        'echo': 'Echo (Male)', 
        'fable': 'Fable (British Male)',
        'onyx': 'Onyx (Deep Male)',
        'nova': 'Nova (Female)',
        'shimmer': 'Shimmer (Soft Female)'
    }
    # Multiple ethics PDFs configuration
    ETHICS_PDF_FILES = [
        "Islamic_Ethics.pdf",
        "Islamic_Ethics2.pdf", 
        "reforming_modernity.pdf"
    ]

# Initialize OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

def load_logo_from_assets() -> Optional[str]:
    """Load logo from assets folder and encode as base64"""
    possible_paths = [
        Path("assets") / "logo.png",
        Path("assets") / "logo.jpg", 
        Path("assets") / "logo.jpeg",
        Path("assets") / "logo.svg",
        Path("assets") / "roehampton_logo.png",
        Path("assets") / "university_logo.png"
    ]
    
    for logo_path in possible_paths:
        if logo_path.exists():
            try:
                with open(logo_path, "rb") as img_file:
                    img_bytes = img_file.read()
                    img_base64 = base64.b64encode(img_bytes).decode()
                    logger.info(f"Successfully loaded logo from: {logo_path}")
                    return img_base64
            except Exception as e:
                logger.warning(f"Error loading logo from {logo_path}: {e}")
                continue
    
    logger.info("No logo found in assets folder")
    return None 

# Page configuration
st.set_page_config(
    page_title=Config.PROJECT_NAME,
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': f"# {Config.PROJECT_NAME}\nComprehensive ethics guidance from Islamic and contemporary perspectives"
    }
)

def initialize_session_state() -> None:
    """Initialize session state for ethics chat"""
    # Audio settings
    if 'audio_enabled' not in st.session_state:
        st.session_state.audio_enabled = True
    if 'selected_voice' not in st.session_state:
        st.session_state.selected_voice = Config.TTS_VOICE
    if 'audio_responses' not in st.session_state:
        st.session_state.audio_responses = {}
    
    # Set dummy authentication data for ethics handler
    if 'student_id' not in st.session_state:
        st.session_state.student_id = "ETHICS_USER"
    if 'student_data' not in st.session_state:
        st.session_state.student_data = {
            'programme': 'Comprehensive Ethics Assistant',
            'code': 'ETHICS'
        }
    
    # Initialize ethics session state if available
    if ETHICS_AVAILABLE:
        initialize_ethics_session_state()
    
    # Initialize language system
    init_language_system()

def generate_audio_response(text: str, voice: str = None) -> Optional[bytes]:
    """Generate audio response using OpenAI TTS"""
    if not client:
        logger.error("OpenAI client not initialized")
        return None
    
    if not text or not text.strip():
        logger.error("No text provided for audio generation")
        return None
    
    # Clean text for TTS
    clean_text = clean_text_for_tts(text)
    selected_voice = voice or st.session_state.get('selected_voice', Config.TTS_VOICE)
    
    try:
        response = client.audio.speech.create(
            model=Config.TTS_MODEL,
            voice=selected_voice,
            input=clean_text,
            response_format="mp3"
        )
        return response.content
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None

def clean_text_for_tts(text: str) -> str:
    """Clean text for text-to-speech by removing markdown and formatting"""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
    text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # headers
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # code blocks
    text = re.sub(r'`([^`]+)`', r'\1', text)      # inline code
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    
    # Remove emojis and special characters
    text = re.sub(r'[🔑📄📚⚠️❌✅🤖🙋📊💾⏱️🔧🗑️🔄🔍🚨📁🎓📋🆔🔐]', '', text)
    
    # Clean up spaces and line breaks
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure proper sentence ending
    text = text.strip()
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    
    return text

def create_audio_player(audio_bytes: bytes, key: str = None) -> str:
    """Create an HTML audio player with the audio data"""
    if not audio_bytes:
        return ""
    
    audio_base64 = base64.b64encode(audio_bytes).decode()
    
    if not key:
        key = f"audio_{int(time.time() * 1000)}"
    
    audio_html = f"""
    <div class="audio-player-container" style="margin: 10px 0;">
        <div class="audio-controls" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 25px;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.3);
        ">
            <div style="color: white; font-weight: 500; display: flex; align-items: center; gap: 8px;">
                🔊 <span style="font-size: 14px;">{t('audio_response', default='Audio Response')}</span>
            </div>
            <audio controls style="
                height: 35px;
                border-radius: 17px;
                outline: none;
                flex: 1;
                min-width: 200px;
            ">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
                {t('audio_not_supported', default='Your browser does not support audio playback.')}
            </audio>
        </div>
    </div>
    """
    
    return audio_html

def render_voice_selector():
    """Render voice selector in sidebar"""
    st.markdown(f"🎤 {t('voice_settings', default='Voice Settings')}")
    
    # Audio toggle
    current_audio_state = st.session_state.get('audio_enabled', True)
    audio_enabled = st.checkbox(
        f"🔊 {t('enable_audio', default='Enable Audio Responses')}", 
        value=current_audio_state,
        help=t('audio_help', default='Toggle audio responses for accessibility')
    )
    st.session_state.audio_enabled = audio_enabled
    
    if audio_enabled:
        # Voice selection
        voice_options = list(Config.SUPPORTED_VOICES.keys())
        current_voice = st.session_state.get('selected_voice', Config.TTS_VOICE)
        
        try:
            current_index = voice_options.index(current_voice)
        except ValueError:
            current_index = 0
        
        selected_voice = st.selectbox(
            f"🎭 {t('select_voice', default='Select Voice')}", 
            options=voice_options,
            format_func=lambda x: Config.SUPPORTED_VOICES[x],
            index=current_index,
            help=t('voice_help', default='Choose the voice for audio responses')
        )
        
        st.session_state.selected_voice = selected_voice
        
        # Test voice button
        if st.button(f"🎵 {t('test_voice', default='Test Voice')}", type="secondary"):
            test_text = t('test_audio_text', default='Hello! This is how I will sound when reading responses to you.')
            
            with st.spinner(t('generating_audio', default='Generating audio...')):
                audio_bytes = generate_audio_response(test_text, selected_voice)
                
            if audio_bytes:
                audio_html = create_audio_player(audio_bytes, key="voice_test")
                st.markdown(audio_html, unsafe_allow_html=True)
                st.success(t('audio_ready', default='Audio ready!'))
            else:
                st.error(t('audio_error', default='Failed to generate audio'))
    else:
        st.info(t('audio_disabled', default='Audio responses are disabled'))

def read_document(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read PDF document (ethics-only version)"""
    try:
        if file_path.suffix.lower() == '.pdf':
            return read_pdf(file_path)
        else:
            return None, {'error': f'Unsupported file type: {file_path.suffix}. Only PDF supported.'}
    except Exception as e:
        logger.error(f"Error reading document {file_path}: {e}")
        return None, {'error': str(e)}

def read_pdf(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read PDF file and extract metadata"""
    try:
        reader = PdfReader(str(file_path))
        text = ""
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                continue
        
        metadata = {
            'total_pages': total_pages,
            'file_size': file_path.stat().st_size,
            'file_type': 'PDF',
            'word_count': len(text.split()) if text else 0,
            'character_count': len(text),
        }
        
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name}: {e}")
        return None, {'error': str(e)}

def render_sidebar():
    """Render sidebar with controls"""
    with st.sidebar:
        # Language selector
        st.markdown(f"🌐 {t('language_selector', default='Language')}")
        render_language_selector()
        
        # DEBUG: Show current language
        st.write(f"**{t('debug_current_language', default='Debug - Current Language')}:** {st.session_state.get('language', 'NOT SET')}")
        
        # Voice settings
        render_voice_selector()
        
        st.markdown("---")
        
        # System status - Updated for file selector
        st.markdown("📊 System Status")
        
        if ETHICS_AVAILABLE:
            st.success("✅ Ethics System with File Selection Available")
            
            # Show which PDFs are available
            from pathlib import Path
            from ethics_handler import get_available_pdfs, EthicsConfig
            
            data_folder = Path("data")
            available_pdfs = get_available_pdfs()
            
            if available_pdfs:
                st.success(f"✅ Available Documents: {len(available_pdfs)}/{len(EthicsConfig.ETHICS_PDF_FILES)}")
                for pdf in available_pdfs:
                    display_name = EthicsConfig.PDF_DISPLAY_NAMES.get(pdf, pdf)
                    st.write(f"   {display_name}")
            
            missing_pdfs = [pdf for pdf in EthicsConfig.ETHICS_PDF_FILES if pdf not in available_pdfs]
            if missing_pdfs:
                st.warning(f"⚠️ Missing Documents: {len(missing_pdfs)}")
                for pdf in missing_pdfs:
                    display_name = EthicsConfig.PDF_DISPLAY_NAMES.get(pdf, pdf)
                    st.write(f"   ❌ {display_name}")
        else:
            st.error("❌ Ethics System Not Available")
        
        if OPENAI_API_KEY:
            st.success("✅ AI Service Connected")
        else:
            st.error("❌ AI Service Not Available")
        
        st.markdown("---")
        
        # File selection info
        if ETHICS_AVAILABLE:
            st.markdown("📁 Document Selection")
            st.info(t('file_selector_info', default='Use the document selector above to choose which ethics source to chat with, or select "All Documents" for comprehensive guidance.'))
        
        st.markdown("---")
        
        # Quick actions
        st.markdown(f"⚡ {t('quick_actions', default='Quick Actions')}")
        
        if st.button(f"🗑️ {t('clear_all_chats', default='Clear All Chats')}", use_container_width=True, type="secondary"):
            # Clear all chat sessions
            keys_to_clear = [key for key in st.session_state.keys() if key.startswith('messages_') or key.startswith('audio_responses_')]
            for key in keys_to_clear:
                del st.session_state[key]
            st.success(t('all_chats_cleared', default='All chat sessions cleared!'))
            st.rerun()

def get_simplified_css() -> str:
    """Get simplified CSS for comprehensive ethics interface"""
    base_css = """
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;600;700&display=swap');
        
        /* Roehampton University Brand Colors - Updated for comprehensive ethics */
    :root {
        --roehampton-green: #2F4F6F;            /* Now Slate Blue */
        --roehampton-dark-green: #1D2F3F;       /* Deep Navy */
        --roehampton-light-green: #7A9EBB;      /* Muted Sky Blue */
        --roehampton-navy: #BFD8E5;             /* Soft Pale Blue */
        --roehampton-charcoal: #2B2F38;         /* Dark Charcoal */
        --background-light: #F5F7FA;            /* Light Grey Background */
        --background-white: #FFFFFF;            /* White */
        --text-primary: #2B2F38;                /* Charcoal Text */
        --text-secondary: #6C757D;              /* Soft Grey */
        --border-color: #DDE3E9;                /* Light Blue-Grey Border */
        --shadow: 0 2px 4px rgba(47, 79, 111, 0.08);
        --shadow-lg: 0 8px 25px rgba(47, 79, 111, 0.12);
        --accent-islamic: #008751;               /* Islamic Green */
        --accent-modern: #6366F1;               /* Modern Purple */
        }
        
        /* Global styling */
        .main, .sidebar .sidebar-content {
            font-family: 'Inter', 'Noto Sans Arabic', 'Arial', sans-serif !important;
            background-color: var(--background-light);
        }
        
        /* Arabic text support */
        [lang="ar"], .arabic-text {
            font-family: 'Noto Sans Arabic', 'Arial', 'Tahoma', sans-serif !important;
            line-height: 1.8 !important;
            text-align: right !important;
        }
        
        /* Header styling - Enhanced for comprehensive ethics */
        .ethics-header {
            background: linear-gradient(135deg, var(--roehampton-green), var(--roehampton-dark-green), var(--accent-islamic));
            padding: 2.5rem 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }
        
        .ethics-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(0,135,81,0.1), rgba(99,102,241,0.1));
            pointer-events: none;
        }
     
        /* Chat interface prominence */
        .chat-section {
            background: var(--background-white);
            border-radius: 15px;
            padding: 2rem;
            margin: 2rem 0;
            border: 2px solid var(--roehampton-green);
            box-shadow: var(--shadow-lg);
        }
        
        .chat-welcome {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #f0fdf9, #e8f5f0, #f3e8ff);
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid var(--roehampton-light-green);
        }
        
        .chat-welcome h3 {
            color: var(--roehampton-green);
            margin-bottom: 1rem;
        }
        
        .stChatInput > div {
            border: 2px solid var(--roehampton-green) !important;
            border-radius: 25px !important;
            background: var(--background-white) !important;
        }
        
        .logo-title-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .roehampton-logo {
            height: 90px;
            width: auto;
            background: white;
            padding: 0.75rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .ethics-header h1 {
            margin: 0;
            font-weight: 700;
            font-size: 2.8rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .ethics-header p {
            margin: 0;
            opacity: 0.95;
            font-size: 1.3rem;
            font-weight: 400;
        }
        
        /* Multi-source indicator */
        .source-indicator {
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-top: 1rem;
            display: inline-block;
        }
        
        /* Button styling - Enhanced */
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            font-size: 1.1rem;
            padding: 0.8rem 1.5rem;
        }
        
        .stButton > button[data-baseweb="button"][kind="primary"] {
            background: linear-gradient(135deg, var(--roehampton-green), var(--accent-islamic));
            color: white;
            box-shadow: var(--shadow);
        }
        
        .stButton > button[data-baseweb="button"][kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .stButton > button[data-baseweb="button"][kind="secondary"] {
            background: white;
            color: var(--roehampton-green);
            border: 2px solid var(--roehampton-green);
        }
        
        .stButton > button[data-baseweb="button"][kind="secondary"]:hover {
            background: var(--roehampton-green);
            color: white;
            transform: translateY(-1px);
        }
        
        /* Audio player styling */
        .audio-player-container {
            margin: 15px 0;
            padding: 0;
        }
        
        .audio-controls {
            background: linear-gradient(135deg, var(--roehampton-green), var(--accent-islamic));
            border-radius: 25px;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: var(--shadow-lg);
            transition: all 0.3s ease;
        }
        
        .audio-controls:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 135, 81, 0.3);
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid var(--border-color);
            padding: 0.75rem 1rem;
            font-size: 1rem;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--roehampton-green);
            box-shadow: 0 0 0 3px rgba(0, 135, 81, 0.1);
        }
        
        /* Status indicators - Enhanced for multiple sources */
        .status-success {
            background: linear-gradient(135deg, var(--accent-islamic), var(--roehampton-green));
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: var(--shadow);
        }
        
        .status-warning {
            background: linear-gradient(135deg, #F59E0B, #D97706);
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-error {
            background: linear-gradient(135deg, #E74C3C, #C0392B);
            color: white;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* PDF indicator badges */
        .pdf-badge {
            background: rgba(255,255,255,0.9);
            color: var(--roehampton-green);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 0.2rem;
            display: inline-block;
            box-shadow: var(--shadow);
        }
        
        /* Reduce sidebar width */
        .css-1d391kg {
            width: 250px !important;
        }

        .css-1lcbmhc {
            width: 250px !important;
            min-width: 250px !important;
        }

        /* Reduce sidebar padding */
        .css-1lcbmhc .css-1outpf7 {
            padding-top: 5rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }

        /* Compact sidebar sections */
        .sidebar .block-container {
            padding-top: 5rem !important;
            padding-bottom: 5rem !important;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .ethics-header h1 {
                font-size: 2rem;
            }
            
            .logo-title-container {
                flex-direction: column;
                gap: 1rem;
            }
            
            .roehampton-logo {
                height: 70px;
            }
        }
    </style>
    """
    
    # Add RTL support
    from localization import get_rtl_css
    rtl_css = get_rtl_css()
    
    return base_css + rtl_css

def main():
    """Ethics application with file selection feature"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Apply CSS
        st.markdown(get_simplified_css(), unsafe_allow_html=True)
        
        # Render sidebar
        render_sidebar()
        
        # Main content
        if not ETHICS_AVAILABLE:
            st.error(t('ethics_system_not_available', default='❌ Ethics system with file selection is not available'))
            st.info(t('ensure_ethics_files_selector', default="Please ensure 'ethics_handler.py' exists and the ethics PDF files are in your data folder."))
            st.stop()
        
        # Load logo
        logo_base64 = load_logo_from_assets()
        
        # Check PDF availability
        from ethics_handler import get_available_pdfs, EthicsConfig
        available_pdfs = get_available_pdfs()
        
        # Create PDF badges for available documents
        pdf_badges = ""
        for pdf in available_pdfs:
            pdf_name = EthicsConfig.PDF_DISPLAY_NAMES.get(pdf, pdf.replace('.pdf', '').replace('_', ' ').title())
            pdf_badges += f'<span class="pdf-badge">{pdf_name}</span>'
        
        if logo_base64:
            st.markdown(f"""
            <div class="ethics-header">
                <div class="logo-title-container">
                    <div>
                        <h1>{t('ethics_file_selector_title', default='AI Ethics Assistant with Document Selection')}</h1>
                    </div>
                </div>
                <p>{t('file_selector_subtitle', default='Choose specific documents or combine multiple sources for comprehensive ethical guidance')}</p>
                <div class="source-indicator">
                    📚 {len(available_pdfs)} {t('documents_available', default='documents available')} | 🎯 {t('selective_chat', default='Selective Chat Mode')}
                </div>
                <div style="margin-top: 1rem;">
                    {pdf_badges}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ethics-header">
                <h1>📋 {t('ethics_file_selector_title', default='AI Ethics Assistant with Document Selection')}</h1>
                <p>{t('file_selector_subtitle', default='Choose specific documents or combine multiple sources for comprehensive ethical guidance')}</p>
                <div class="source-indicator">
                    📚 {len(available_pdfs)} {t('documents_available', default='documents available')} | 🎯 {t('selective_chat', default='Selective Chat Mode')}
                </div>
                <div style="margin-top: 1rem;">
                    {pdf_badges}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show helpful information about the file selector feature
        with st.expander(f"ℹ️ {t('how_file_selection_works', default='How Document Selection Works')}", expanded=False):
            st.markdown(f"""
            **{t('individual_documents', default='Individual Documents')}:**
            - 📗 **Islamic Ethics (Volume 1)**: {t('islamic_vol1_desc', default='Core Islamic ethical principles and foundations')}
            - 📘 **Islamic Ethics (Volume 2)**: {t('islamic_vol2_desc', default='Advanced Islamic ethical applications and cases')}
            - 📙 **Reforming Modernity**: {t('reforming_desc', default='Contemporary ethical frameworks and modern perspectives')}
            
            **📚 {t('all_documents_combined', default='All Documents Combined')}**: {t('comprehensive_desc', default='Access all sources simultaneously for comprehensive, multi-perspective guidance')}
            
            **{t('benefits', default='Benefits')}:**
            - 🎯 {t('focused_expertise', default='Get focused expertise from specific traditions')}
            - 🔄 {t('easy_switching', default='Easily switch between different ethical perspectives')}
            - 💬 {t('separate_conversations', default='Maintain separate conversation histories for each source')}
            - 🔍 {t('comparative_analysis', default='Compare different approaches by chatting with multiple sources')}
            """)
        
        # Show PDF status if some are missing
        if len(available_pdfs) < len(Config.ETHICS_PDF_FILES):
            missing_pdfs = [pdf for pdf in Config.ETHICS_PDF_FILES if pdf not in available_pdfs]
            missing_display = [EthicsConfig.PDF_DISPLAY_NAMES.get(pdf, pdf) for pdf in missing_pdfs]
            st.warning(f"⚠️ {t('some_documents_missing', default='Some documents are missing')}: {', '.join(missing_display)}")
            st.info(t('app_works_with_available', default='The application will work with the available documents.'))
        
        if not available_pdfs:
            st.error(t('no_documents_available', default='❌ No documents are available. Please add PDF files to the data folder.'))
            st.stop()
        
        # Render ethics chat interface with file selection
        render_ethics_chat_interface()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"🚨 **{t('application_error', default='Application Error')}**: {str(e)}")
        
        if st.checkbox(t('show_detailed_error', default='Show detailed error information')):
            import traceback
            st.code(traceback.format_exc())
        
        st.info(t('refresh_page', default='Please try refreshing the page or check your configuration.'))
        
        if st.button(f"🔄 {t('reset_application', default='Reset Application')}"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == '__main__':
    main()