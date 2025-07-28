import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any, List
import logging
import glob

# Import our localization system
from localization import language_manager, t, init_language_system, render_language_selector, get_rtl_css, get_language_specific_ai_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - Centralized settings
class Config:
    PROJECT_NAME = "AI Multi-Document Assistant"
    COMPANY_NAME = "Powered by AI"
    DATA_FOLDER = "data"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    MAX_CONTENT_LENGTH = 15000  # Increased for multiple docs
    PREVIEW_LENGTH = 800
    SUPPORTED_EXTENSIONS = ['.pdf', '.docx']

# Initialize OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# Page configuration with better metadata
st.set_page_config(
    page_title=Config.PROJECT_NAME,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': f"# {Config.PROJECT_NAME}\nChat with multiple documents using AI"
    }
)

def get_enhanced_css() -> str:
    """Get enhanced CSS with RTL support"""
    base_css = """
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;600;700&display=swap');
        
        /* Root variables for consistent theming */
        :root {
            --primary-color: #1f2937;
            --secondary-color: #3b82f6;
            --success-color: #10b981;
            --error-color: #ef4444;
            --warning-color: #f59e0b;
            --info-color: #8b5cf6;
            --background-light: #f8fafc;
            --background-dark: #ffffff;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --border-color: #e5e7eb;
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Global font with multi-language support */
        .main, .sidebar .sidebar-content {
            font-family: 'Inter', 'Noto Sans Arabic', 'Arial', sans-serif !important;
        }
        
        /* Arabic text specific styling */
        [lang="ar"], .arabic-text {
            font-family: 'Noto Sans Arabic', 'Arial', 'Tahoma', sans-serif !important;
            line-height: 1.8 !important;
            text-align: right !important;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, var(--secondary-color), var(--info-color));
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
        
        /* Language selector styling */
        .language-selector {
            margin-bottom: 1rem;
            padding: 1rem;
            background: var(--background-light);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        /* Document source indicator */
        .doc-source {
            background: linear-gradient(135deg, var(--info-color), #7c3aed);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
            margin: 0.5rem 0;
            display: inline-block;
        }
        
        /* Document library styling */
        .doc-item {
            background: var(--background-light);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            transition: all 0.2s ease;
        }
        
        .doc-item:hover {
            border-color: var(--secondary-color);
            box-shadow: var(--shadow);
        }
        
        .doc-name {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }
        
        .doc-meta {
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
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
        
        .status-info {
            background: linear-gradient(135deg, var(--info-color), #7c3aed);
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
            
            .doc-meta {
                flex-direction: column;
                gap: 0.25rem;
            }
        }
    </style>
    """
    
    # Add RTL-specific CSS if needed
    rtl_css = get_rtl_css()
    
    return base_css + rtl_css

def initialize_session_state() -> None:
    """Initialize session state variables with proper typing"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'documents' not in st.session_state:
        st.session_state.documents = {}
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    if 'total_metadata' not in st.session_state:
        st.session_state.total_metadata = {}
    
    # Initialize language system
    init_language_system()

def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Fix common encoding issues
    text = text.replace('\u2019', "'")  # Right single quotation mark
    text = text.replace('\u2018', "'")  # Left single quotation mark
    text = text.replace('\u201c', '"')  # Left double quotation mark
    text = text.replace('\u201d', '"')  # Right double quotation mark
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '-')  # Em dash
    text = text.replace('\u2026', '...')  # Horizontal ellipsis
    
    # Remove excessive line breaks but preserve paragraph structure
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    
    return text

def extract_docx_with_mammoth(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Alternative DOCX extraction using mammoth library (fallback method)"""
    try:
        import mammoth
        
        with open(file_path, "rb") as docx_file:
            result = mammoth.extract_raw_text(docx_file)
            text = result.value
            
            if result.messages:
                logger.warning(f"Mammoth extraction warnings for {file_path.name}: {result.messages}")
            
            # Clean the text
            text = clean_text(text)
            
            # Basic metadata
            metadata = {
                'file_size': file_path.stat().st_size,
                'file_type': 'Word Document (Mammoth)',
                'word_count': len(text.split()) if text else 0,
                'character_count': len(text),
                'extraction_method': 'mammoth'
            }
            
            return text if text.strip() else None, metadata
            
    except ImportError:
        logger.warning("Mammoth library not available for enhanced DOCX extraction")
        return None, {}
    except Exception as e:
        logger.error(f"Mammoth extraction failed for {file_path.name}: {e}")
        return None, {}

def read_pdf(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read PDF file and extract metadata"""
    try:
        reader = PdfReader(str(file_path))
        text = ""
        total_pages = len(reader.pages)
        
        # Extract text
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1} in {file_path.name}: {e}")
                continue
        
        # Metadata
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
        return None, {}

def read_docx(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read DOCX file with multiple extraction methods for better compatibility"""
    
    # Method 1: Try enhanced python-docx extraction
    try:
        doc = Document(str(file_path))
        text_parts = []
        paragraph_count = 0
        
        # Extract text from paragraphs with better formatting
        for paragraph in doc.paragraphs:
            para_text = paragraph.text.strip()
            if para_text:
                # Handle different paragraph styles
                if paragraph.style.name.startswith('Heading'):
                    text_parts.append(f"\n## {para_text}\n")
                else:
                    text_parts.append(para_text)
                paragraph_count += 1
        
        # Extract text from tables with structure preservation
        table_count = len(doc.tables)
        for table_idx, table in enumerate(doc.tables):
            text_parts.append(f"\n--- Table {table_idx + 1} ---")
            for row_idx, row in enumerate(table.rows):
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    text_parts.append(" | ".join(row_text))
            text_parts.append("--- End Table ---\n")
        
        # Extract text from headers and footers
        for section in doc.sections:
            # Header
            if section.header:
                for paragraph in section.header.paragraphs:
                    header_text = paragraph.text.strip()
                    if header_text:
                        text_parts.append(f"[Header: {header_text}]")
            
            # Footer
            if section.footer:
                for paragraph in section.footer.paragraphs:
                    footer_text = paragraph.text.strip()
                    if footer_text:
                        text_parts.append(f"[Footer: {footer_text}]")
        
        # Combine all text parts
        full_text = "\n".join(text_parts)
        
        # Clean up the text
        full_text = clean_text(full_text)
        
        # If we got good content, return it
        if full_text and len(full_text.strip()) > 50:  # Minimum content threshold
            metadata = {
                'paragraphs': paragraph_count,
                'tables': table_count,
                'file_size': file_path.stat().st_size,
                'file_type': 'Word Document',
                'word_count': len(full_text.split()) if full_text else 0,
                'character_count': len(full_text),
                'extraction_method': 'python-docx'
            }
            return full_text, metadata
        
    except Exception as e:
        logger.warning(f"python-docx extraction failed for {file_path.name}: {e}")
    
    # Method 2: Try mammoth library as fallback
    logger.info(f"Trying alternative extraction method for {file_path.name}")
    mammoth_text, mammoth_metadata = extract_docx_with_mammoth(file_path)
    
    if mammoth_text and len(mammoth_text.strip()) > 50:
        return mammoth_text, mammoth_metadata
    
    # Method 3: Try raw XML extraction as last resort
    try:
        import xml.etree.ElementTree as ET
        from zipfile import ZipFile
        
        logger.info(f"Trying XML extraction for {file_path.name}")
        
        text_parts = []
        with ZipFile(str(file_path), 'r') as docx_zip:
            if 'word/document.xml' in docx_zip.namelist():
                xml_content = docx_zip.read('word/document.xml')
                root = ET.fromstring(xml_content)
                
                # Extract all text nodes
                for text_elem in root.iter():
                    if text_elem.tag.endswith('}t') and text_elem.text:
                        clean_elem_text = text_elem.text.strip()
                        if clean_elem_text and len(clean_elem_text) > 1:
                            text_parts.append(clean_elem_text)
        
        if text_parts:
            full_text = " ".join(text_parts)
            full_text = clean_text(full_text)
            
            if full_text and len(full_text.strip()) > 50:
                metadata = {
                    'file_size': file_path.stat().st_size,
                    'file_type': 'Word Document (XML)',
                    'word_count': len(full_text.split()),
                    'character_count': len(full_text),
                    'extraction_method': 'xml'
                }
                return full_text, metadata
                
    except Exception as xml_e:
        logger.error(f"XML extraction also failed for {file_path.name}: {xml_e}")
    
    # If all methods failed
    logger.error(f"All extraction methods failed for {file_path.name}")
    return None, {
        'file_size': file_path.stat().st_size,
        'file_type': 'Word Document (Failed)',
        'extraction_method': 'failed',
        'error': 'Could not extract text content'
    }

@st.cache_data(show_spinner=False)
def load_all_documents() -> Tuple[Dict[str, Dict], str, Dict[str, Any]]:
    """
    Load all documents from the data folder with detailed debugging
    
    Returns:
        Tuple of (documents_dict, status_message, total_metadata)
    """
    data_path = Path(Config.DATA_FOLDER)
    
    if not data_path.exists():
        return {}, t('data_folder_not_found', folder=Config.DATA_FOLDER), {}
    
    documents = {}
    total_files = 0
    successful_loads = 0
    failed_loads = []
    total_words = 0
    total_pages = 0
    total_size = 0
    
    # Find all supported files
    supported_files = []
    for ext in Config.SUPPORTED_EXTENSIONS:
        found_files = list(data_path.glob(f"*{ext}"))
        supported_files.extend(found_files)
        logger.info(f"Found {len(found_files)} {ext} files")
    
    logger.info(f"Total supported files found: {len(supported_files)}")
    
    if not supported_files:
        # List all files in the directory for debugging
        all_files = list(data_path.glob("*"))
        file_list = [f.name for f in all_files]
        return {}, t('no_supported_docs', folder=Config.DATA_FOLDER, files=file_list), {}
    
    # Process each file with detailed logging
    for file_path in supported_files:
        total_files += 1
        logger.info(f"Processing: {file_path.name}")
        
        try:
            if file_path.suffix.lower() == '.pdf':
                logger.info(f"Reading PDF: {file_path.name}")
                content, metadata = read_pdf(file_path)
            elif file_path.suffix.lower() == '.docx':
                logger.info(f"Reading DOCX: {file_path.name}")
                content, metadata = read_docx(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_path.name}")
                continue
            
            if content and content.strip():
                documents[file_path.name] = {
                    'content': content,
                    'metadata': metadata,
                    'file_path': str(file_path)
                }
                successful_loads += 1
                total_words += metadata.get('word_count', 0)
                total_pages += metadata.get('total_pages', metadata.get('paragraphs', 0))
                total_size += metadata.get('file_size', 0)
                logger.info(f"✅ Successfully loaded {file_path.name} - {metadata.get('word_count', 0)} words")
            else:
                failed_loads.append({
                    'file': file_path.name,
                    'reason': 'No content extracted',
                    'metadata': metadata
                })
                logger.warning(f"❌ Failed to extract content from {file_path.name}")
            
        except Exception as e:
            failed_loads.append({
                'file': file_path.name,
                'reason': str(e),
                'metadata': {}
            })
            logger.error(f"Error processing {file_path.name}: {e}")
            continue
    
    # Calculate total metadata
    total_metadata = {
        'total_files': total_files,
        'successful_loads': successful_loads,
        'failed_loads': len(failed_loads),
        'failed_files': failed_loads,
        'total_words': total_words,
        'total_pages': total_pages,
        'total_size': total_size,
        'estimated_reading_time': max(1, total_words // 200)
    }
    
    if successful_loads == 0:
        status_message = t('failed_to_load', errors=failed_loads)
    elif failed_loads:
        status_message = t('loaded_docs_status', success=successful_loads, total=total_files, failed=len(failed_loads))
    else:
        status_message = t('all_docs_loaded', success=successful_loads, total=total_files)
    
    return documents, status_message, total_metadata

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

def search_documents(question: str, documents: Dict[str, Dict]) -> str:
    """
    Search across all documents and generate AI response with multi-language support
    
    Args:
        question: User's question
        documents: Dictionary of all loaded documents
        
    Returns:
        AI response string with source attribution
    """
    # Handle greetings in multiple languages
    greetings = {
        'en': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
        'ar': ['مرحبا', 'أهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير'],
        'fr': ['bonjour', 'salut', 'bonsoir', 'coucou'],
        'es': ['hola', 'buenos días', 'buenas tardes', 'buenas noches']
    }
    
    question_clean = question.lower().strip()
    current_lang = language_manager.current_language
    
    # Check for greetings in current language
    is_greeting = False
    for lang, greeting_list in greetings.items():
        if any(greeting in question_clean for greeting in greeting_list):
            is_greeting = True
            break
    
    if is_greeting:
        doc_count = len(documents)
        doc_list = ", ".join(list(documents.keys())[:3])
        if doc_count > 3:
            doc_list += f" {t('and_more')}"
        
        return t('hello_response', 
                app_name=t('app_title'),
                doc_count=doc_count,
                doc_list=doc_list)
    
    if not client:
        return f"🔑 **{t('api_key_missing')}**"
    
    if not documents:
        return f"📄 **{t('no_docs_error')}**"
    
    try:
        # Prepare document content for search
        combined_content = ""
        doc_sections = []
        
        for doc_name, doc_data in documents.items():
            content = doc_data['content'][:Config.MAX_CONTENT_LENGTH // len(documents)]  # Distribute content evenly
            
            doc_section = f"\n\n=== DOCUMENT: {doc_name} ===\n{content}\n=== END OF {doc_name} ==="
            combined_content += doc_section
            doc_sections.append({
                'name': doc_name,
                'content': content,
                'type': doc_data['metadata'].get('file_type', 'Unknown')
            })
        
        # Create document info for prompt
        documents_info = "\n".join([f"- {doc['name']} ({doc['type']})" for doc in doc_sections])
        
        # Get language-specific system prompt
        system_prompt = get_language_specific_ai_prompt(documents_info, combined_content)
        
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
            return f"⚠️ **{t('rate_limit_error')}**"
        elif "authentication" in str(e).lower() or "api_key" in str(e).lower():
            return f"🔑 **{t('auth_error')}**"
        elif "invalid" in str(e).lower():
            return f"❌ **{t('invalid_request', error=str(e))}**"
        else:
            logger.error(f"Error generating AI response: {e}")
            return f"❌ **{t('response_error', error=str(e))}**"

def render_sidebar() -> None:
    """Render enhanced sidebar with multi-document information and language selector"""
    with st.sidebar:
        # Language selector at the top
        st.markdown(f"### 🌐 {t('language_selector')}")
        render_language_selector()
        
        st.markdown("---")
        
        st.markdown(f"### 📚 {t('document_library')}")
        
        # Load documents if not already loaded
        if not st.session_state.documents_loaded:
            with st.spinner(t('loading_docs')):
                documents, message, total_metadata = load_all_documents()
                st.session_state.documents = documents
                st.session_state.documents_loaded = len(documents) > 0
                st.session_state.total_metadata = total_metadata
        
        # Display loading status
        if st.session_state.documents_loaded:
            total_meta = st.session_state.total_metadata
            
            st.markdown(f"""
            <div class="status-success">
                ✅ {t('docs_loaded', count=total_meta['successful_loads'])}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Overall statistics
            st.markdown(f"""
            <div class="sidebar-info">
                <div class="info-item">
                    <span class="info-label">📁 {t('total_files')}:</span>
                    <span class="info-value">{total_meta['successful_loads']}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📝 {t('total_words')}:</span>
                    <span class="info-value">{total_meta['total_words']:,}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📊 {t('total_pages')}:</span>
                    <span class="info-value">{total_meta['total_pages']}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">💾 {t('total_size')}:</span>
                    <span class="info-value">{format_file_size(total_meta['total_size'])}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">⏱️ {t('reading_time')}:</span>
                    <span class="info-value">~{total_meta['estimated_reading_time']} {t('minutes')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Individual document list
            with st.expander(f"📄 {t('document_details')}", expanded=False):
                for doc_name, doc_data in st.session_state.documents.items():
                    metadata = doc_data['metadata']
                    st.markdown(f"""
                    <div class="doc-item">
                        <div class="doc-name">📄 {doc_name}</div>
                        <div class="doc-meta">
                            <span>{t('file_type')}: {metadata.get('file_type', 'Unknown')}</span>
                            <span>{t('words')}: {metadata.get('word_count', 0):,}</span>
                            <span>{t('size')}: {format_file_size(metadata.get('file_size', 0))}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
        else:
            st.markdown(f"""
            <div class="status-error">
                ❌ {t('no_docs_loaded')}
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"📁 {t('looking_in', folder=f'`{Config.DATA_FOLDER}/`')}")
            st.info(t('supported_formats'))
        
        st.markdown("---")
        
        # Controls
        st.markdown(f"### 🔧 {t('controls')}")
        
        # Clear chat button
        if st.button(f"🗑️ {t('clear_chat')}", type="secondary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Reload documents button
        if st.button(f"🔄 {t('reload_docs')}", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.session_state.documents = {}
            st.session_state.documents_loaded = False
            st.session_state.total_metadata = {}
            st.rerun()

def render_chat_interface() -> None:
    """Render the main chat interface with multi-language support"""
    st.markdown(f"""
    <div class="main-header">
        <h1>📚 {t('app_title')}</h1>
        <p>{t('app_subtitle')} • {t('powered_by')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check prerequisites
    if not OPENAI_API_KEY:
        st.error(f"🔑 **{t('api_key_not_found')}**")
        st.info(t('add_api_key'))
        st.code("OPENAI_API_KEY=sk-your-api-key-here")
        st.stop()
    
    if not st.session_state.documents_loaded:
        st.error(f"📚 **{t('no_docs_error')}**")
        st.info(t('looking_for_files', folder=f"`{Config.DATA_FOLDER}/`"))
        return
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Empty state
            doc_count = len(st.session_state.documents)
            doc_names = list(st.session_state.documents.keys())
            
            st.markdown(f"""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <h3>{t('ready_to_search', count=doc_count)}</h3>
                <p>{t('search_through', docs=f"<strong>{', '.join(doc_names[:3])}</strong>{f' {t("and_more")}' if doc_count > 3 else ''}")}</p>
                <p>{t('try_asking')}</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>"{t('example_1')}"</li>
                    <li>"{t('example_2')}"</li>
                    <li>"{t('example_3')}"</li>
                    <li>"{t('example_4')}"</li>
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
                            🙋 {t('you')}
                        </div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <div class="message-header">
                            🤖 {t('ai_assistant')}
                        </div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

def handle_user_input() -> None:
    """Handle user input and generate AI responses with multi-language support"""
    # Chat input with localized placeholder
    if prompt := st.chat_input(t('search_placeholder')):
        # Validate input
        if not prompt.strip():
            st.warning(f"⚠️ {t('enter_question')}")
            return
        
        # Add user message
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": time.time()
        })
        
        # Generate AI response with loading indicator
        with st.spinner(t('searching')):
            response = search_documents(prompt, st.session_state.documents)
        
        # Add AI response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": time.time()
        })
        
        # Rerun to update the interface
        st.rerun()

def main() -> None:
    """Main application function with proper error handling and multi-language support"""
    try:
        # Initialize session state and language system
        initialize_session_state()
        
        # Apply enhanced CSS with RTL support
        st.markdown(get_enhanced_css(), unsafe_allow_html=True)
        
        # Render sidebar
        render_sidebar()
        
        # Render main chat interface
        render_chat_interface()
        
        # Handle user input
        handle_user_input()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"🚨 **{t('app_error', error=str(e))}**")
        st.info(t('refresh_page'))

if __name__ == '__main__':
    main()