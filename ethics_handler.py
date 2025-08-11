# ethics_handler.py - File Selector Version

import streamlit as st
import os
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from openai import OpenAI
import traceback

# Import from your existing modules
from localization import t

# Configure logging
logger = logging.getLogger(__name__)

def get_openai_client():
    """Get OpenAI client from main app or initialize new one"""
    try:
        # Try to import client from main app
        from app import client
        if client:
            logger.info("Using OpenAI client from main app")
            return client
    except ImportError:
        logger.warning("Could not import client from app")
    
    # Fallback: initialize our own client
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        logger.info("Initializing new OpenAI client")
        return OpenAI(api_key=OPENAI_API_KEY)
    else:
        logger.error("No OpenAI API key found")
        return None

class EthicsConfig:
    """Configuration for ethics document handling"""
    ETHICS_PDF_FILES = [
        "Islamic_Ethics.pdf",
        "Islamic_Ethics2.pdf", 
        "reforming_modernity.pdf"
    ]
    PDF_DISPLAY_NAMES = {
        "Islamic_Ethics.pdf": "📗 Islamic Ethics (Volume 1)",
        "Islamic_Ethics2.pdf": "📘 Islamic Ethics (Volume 2)", 
        "reforming_modernity.pdf": "📙 Reforming Modernity"
    }
    DATA_FOLDER = "data"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    MAX_CONTENT_LENGTH = 15000  # Per document limit
    MAX_TOTAL_CONTENT_LENGTH = 40000  # Total content limit for all documents

def read_pdf_directly(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read PDF file directly using PyPDF2"""
    try:
        from PyPDF2 import PdfReader
        logger.info(f"Reading PDF directly: {file_path}")
        
        reader = PdfReader(str(file_path))
        text = ""
        total_pages = len(reader.pages)
        
        logger.info(f"PDF {file_path.name} has {total_pages} pages")
        
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
                    logger.info(f"Successfully extracted text from page {page_num + 1} of {file_path.name}")
                else:
                    logger.warning(f"No text found on page {page_num + 1} of {file_path.name}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1} of {file_path.name}: {e}")
                continue
        
        metadata = {
            'total_pages': total_pages,
            'file_size': file_path.stat().st_size,
            'file_type': 'PDF',
            'word_count': len(text.split()) if text else 0,
            'character_count': len(text),
            'filename': file_path.name
        }
        
        logger.info(f"Successfully read PDF {file_path.name}. Text length: {len(text)} characters")
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name} directly: {e}")
        return None, {'error': str(e), 'filename': file_path.name}

def load_single_ethics_document(pdf_filename: str) -> Tuple[Optional[str], Dict[str, Any], str]:
    """Load a single ethics document"""
    try:
        pdf_path = Path(EthicsConfig.DATA_FOLDER) / pdf_filename
        
        logger.info(f"Attempting to load single document: {pdf_path}")
        
        if not pdf_path.exists():
            error_msg = f"Ethics document not found: {pdf_filename}"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Check if the file is readable
        if not os.access(pdf_path, os.R_OK):
            error_msg = f"Cannot read ethics document: {pdf_filename} (permission denied)"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Check file size
        file_size = pdf_path.stat().st_size
        logger.info(f"File size: {file_size} bytes")
        
        if file_size == 0:
            error_msg = f"Ethics document is empty: {pdf_filename}"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Try to read PDF directly first
        logger.info(f"Reading {pdf_filename} with PyPDF2")
        content, metadata = read_pdf_directly(pdf_path)
        
        if content and content.strip():
            # Truncate if too long
            if len(content) > EthicsConfig.MAX_CONTENT_LENGTH:
                content = content[:EthicsConfig.MAX_CONTENT_LENGTH] + "\n...(content truncated)..."
                logger.info(f"Truncated {pdf_filename} content to {EthicsConfig.MAX_CONTENT_LENGTH} characters")
            
            logger.info(f"Successfully loaded {pdf_filename}")
            return content, metadata, f"Successfully loaded {pdf_filename}"
        
        # Try importing from app if direct reading failed
        logger.info(f"Direct PDF reading failed for {pdf_filename}, trying app.read_document")
        try:
            from app import read_document
            content, metadata = read_document(pdf_path)
            
            if content and content.strip():
                if len(content) > EthicsConfig.MAX_CONTENT_LENGTH:
                    content = content[:EthicsConfig.MAX_CONTENT_LENGTH] + "\n...(content truncated)..."
                
                logger.info(f"Successfully loaded {pdf_filename} using app.read_document")
                return content, metadata, f"Successfully loaded {pdf_filename}"
            else:
                error_msg = f"Failed to extract content from {pdf_filename}"
                logger.error(error_msg)
                return None, metadata or {}, error_msg
        except ImportError as e:
            logger.warning(f"Cannot import read_document function: {e}")
            error_msg = f"Failed to load {pdf_filename}: import error"
            return None, {}, error_msg
        except Exception as e:
            logger.warning(f"Error using app.read_document for {pdf_filename}: {e}")
            error_msg = f"Failed to load {pdf_filename}: {str(e)}"
            return None, {}, error_msg
            
    except Exception as e:
        error_msg = f"Error loading ethics document {pdf_filename}: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None, {}, error_msg

def load_multiple_ethics_documents() -> Tuple[Optional[Dict[str, str]], Dict[str, Dict[str, Any]], List[str]]:
    """Load all ethics documents and combine them"""
    try:
        all_content = {}
        all_metadata = {}
        messages = []
        
        logger.info("Loading multiple ethics documents")
        
        for pdf_file in EthicsConfig.ETHICS_PDF_FILES:
            pdf_path = Path(EthicsConfig.DATA_FOLDER) / pdf_file
            
            logger.info(f"Attempting to load: {pdf_path}")
            
            if not pdf_path.exists():
                error_msg = f"Ethics document not found: {pdf_file}"
                logger.warning(error_msg)
                messages.append(f"⚠️ {error_msg}")
                continue
            
            # Check if the file is readable
            if not os.access(pdf_path, os.R_OK):
                error_msg = f"Cannot read ethics document: {pdf_file} (permission denied)"
                logger.warning(error_msg)
                messages.append(f"⚠️ {error_msg}")
                continue
            
            # Check file size
            file_size = pdf_path.stat().st_size
            logger.info(f"File {pdf_file} size: {file_size} bytes")
            
            if file_size == 0:
                error_msg = f"Ethics document is empty: {pdf_file}"
                logger.warning(error_msg)
                messages.append(f"⚠️ {error_msg}")
                continue
            
            # Try to read PDF directly first
            logger.info(f"Reading {pdf_file} with PyPDF2")
            content, metadata = read_pdf_directly(pdf_path)
            
            if content and content.strip():
                # Truncate individual document if too long
                if len(content) > EthicsConfig.MAX_CONTENT_LENGTH:
                    content = content[:EthicsConfig.MAX_CONTENT_LENGTH] + "\n...(content truncated)..."
                    logger.info(f"Truncated {pdf_file} content to {EthicsConfig.MAX_CONTENT_LENGTH} characters")
                
                all_content[pdf_file] = content
                all_metadata[pdf_file] = metadata
                messages.append(f"✅ Successfully loaded {pdf_file}")
                logger.info(f"Successfully loaded {pdf_file}")
            else:
                # Try importing from app if direct reading failed
                logger.info(f"Direct PDF reading failed for {pdf_file}, trying app.read_document")
                try:
                    from app import read_document
                    content, metadata = read_document(pdf_path)
                    
                    if content and content.strip():
                        if len(content) > EthicsConfig.MAX_CONTENT_LENGTH:
                            content = content[:EthicsConfig.MAX_CONTENT_LENGTH] + "\n...(content truncated)..."
                        
                        all_content[pdf_file] = content
                        all_metadata[pdf_file] = metadata
                        messages.append(f"✅ Successfully loaded {pdf_file} (using app reader)")
                        logger.info(f"Successfully loaded {pdf_file} using app.read_document")
                    else:
                        error_msg = f"Failed to extract content from {pdf_file}"
                        logger.warning(error_msg)
                        messages.append(f"❌ {error_msg}")
                except ImportError as e:
                    logger.warning(f"Cannot import read_document function: {e}")
                    messages.append(f"❌ Failed to load {pdf_file}: import error")
                except Exception as e:
                    logger.warning(f"Error using app.read_document for {pdf_file}: {e}")
                    messages.append(f"❌ Failed to load {pdf_file}: {str(e)}")
        
        if not all_content:
            error_msg = "No ethics documents could be loaded"
            logger.error(error_msg)
            return None, {}, [f"❌ {error_msg}"]
        
        # Combine all content with document separators
        combined_content = ""
        total_length = 0
        
        for pdf_file, content in all_content.items():
            document_header = f"\n\n{'='*80}\nDOCUMENT: {pdf_file}\n{'='*80}\n\n"
            
            # Check if adding this document would exceed total limit
            addition_length = len(document_header) + len(content)
            if total_length + addition_length > EthicsConfig.MAX_TOTAL_CONTENT_LENGTH:
                remaining_space = EthicsConfig.MAX_TOTAL_CONTENT_LENGTH - total_length - len(document_header)
                if remaining_space > 100:  # Only add if there's meaningful space
                    truncated_content = content[:remaining_space] + "\n...(content truncated due to total length limit)..."
                    combined_content += document_header + truncated_content
                    messages.append(f"⚠️ {pdf_file} was truncated due to total content length limit")
                else:
                    messages.append(f"⚠️ {pdf_file} was skipped due to total content length limit")
                break
            else:
                combined_content += document_header + content
                total_length += addition_length
        
        logger.info(f"Combined content length: {len(combined_content)} characters")
        logger.info(f"Loaded {len(all_content)} documents successfully")
        
        return {"combined": combined_content}, all_metadata, messages
            
    except Exception as e:
        error_msg = f"Error loading ethics documents: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None, {}, [f"❌ {error_msg}"]

def get_available_pdfs() -> List[str]:
    """Get list of available PDF files"""
    available_pdfs = []
    data_folder = Path(EthicsConfig.DATA_FOLDER)
    
    for pdf_file in EthicsConfig.ETHICS_PDF_FILES:
        pdf_path = data_folder / pdf_file
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            available_pdfs.append(pdf_file)
    
    return available_pdfs

def generate_ethics_response(question: str, document_content: str, source_info: str = "") -> str:
    """Generate AI response for ethics-related questions"""
    try:
        logger.info(f"Starting ethics response generation - Source: {source_info}")
        logger.info(f"Question length: {len(question) if question else 'None'}")
        logger.info(f"Document content length: {len(document_content) if document_content else 'None'}")
        
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            error_msg = f"🔑 **{t('api_key_missing', default='OpenAI client not initialized. Please check your API key.')}**"
            logger.error("OpenAI client not available")
            return error_msg
        
        if not document_content or not document_content.strip():
            error_msg = f"📄 **No ethics document content available**"
            logger.error("No document content provided")
            return error_msg
        
        if not question or not question.strip():
            error_msg = f"❓ **No question provided**"
            logger.error("No question provided")
            return error_msg
        
        # Get current language for AI response
        current_language = st.session_state.get('language', 'en')
        logger.info(f"Current language from session state: {current_language}")
        
        # Language-specific instructions for AI
        if current_language == 'ar':
            language_instruction = "يجب أن تجيب باللغة العربية فقط. استخدم اللغة العربية الفصحى في جميع إجاباتك."
        elif current_language == 'fr':
            language_instruction = "Répondez en français uniquement. Utilisez un français formel et académique."
        elif current_language == 'es':
            language_instruction = "Responde en español únicamente. Usa un español formal y académico."
        else:
            language_instruction = "Respond in English only."
        
        logger.info(f"Using content length: {len(document_content)} characters")
        logger.info(f"AI will respond in: {current_language}")
        
        # Determine system prompt based on source
        if "all documents" in source_info.lower() or "multiple" in source_info.lower():
            system_prompt = f"""You are an expert ethics advisor with access to multiple comprehensive ethics documents. You are helping with ethics guidance based on Islamic Ethics materials and Reforming Modernity document.

LANGUAGE INSTRUCTION: {language_instruction}

SOURCE: {source_info}

ETHICS DOCUMENTS CONTENT:
{document_content}

INSTRUCTIONS:
- {language_instruction}
- Answer ethics questions based on the provided ethics documents (Islamic Ethics volumes and Reforming Modernity)
- You have access to multiple comprehensive documents covering different aspects of ethical thinking
- When relevant, reference which specific document or section contains the information you're citing
- Provide thoughtful, well-reasoned ethical guidance that draws from the breadth of materials available
- Compare and contrast different ethical approaches when multiple documents address similar topics
- If Islamic ethics and modern ethical frameworks differ, explain both perspectives respectfully
- Help people understand how different ethical traditions can inform decision-making
- Encourage critical thinking about ethical issues as presented across all the materials
- Be supportive and educational in your approach
- If a question cannot be fully answered from any of the documents, clearly state this and suggest what topics the documents do cover
- Always maintain academic integrity and professional ethics standards
- When appropriate, show how Islamic ethical principles and modern ethical frameworks can complement each other

Remember: Base your responses on the actual content of all provided ethics documents. Draw connections between different ethical approaches when relevant, and provide balanced guidance that respects both traditional Islamic ethics and contemporary ethical thinking. ALWAYS respond in the requested language."""
        else:
            system_prompt = f"""You are an expert ethics advisor focusing on a specific ethics document. You are helping with ethics guidance based on the selected document.

LANGUAGE INSTRUCTION: {language_instruction}

SOURCE: {source_info}

ETHICS DOCUMENT CONTENT:
{document_content}

INSTRUCTIONS:
- {language_instruction}
- Answer ethics questions based ONLY on the provided document: {source_info}
- Focus specifically on the content, concepts, and guidance found in this particular document
- Provide thoughtful, well-reasoned ethical guidance based on what's actually in this specific document
- Reference specific sections, concepts, or examples from this document when relevant
- Help people understand and apply the ethical concepts presented in this specific material
- Encourage critical thinking about ethical issues as presented in this document
- Be supportive and educational in your approach
- If a question cannot be answered from this specific document, clearly state this and suggest what topics this document does cover
- Always maintain academic integrity and professional ethics standards
- Stay focused on the perspective and approach of this particular document

Remember: Base your responses strictly on the actual content of the selected document: {source_info}. If the document has a specific ethical perspective or methodology, emphasize that in your responses. ALWAYS respond in the requested language."""

        logger.info("Making OpenAI API call")
        response = client.chat.completions.create(
            model=EthicsConfig.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=EthicsConfig.MAX_TOKENS,
            temperature=EthicsConfig.TEMPERATURE,
        )
        
        if response and response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content.strip()
            logger.info("Successfully generated ethics response")
            return result
        else:
            error_msg = "❌ **No response generated from OpenAI**"
            logger.error("OpenAI returned empty response")
            return error_msg
        
    except Exception as e:
        error_msg = f"❌ **Error generating response: {str(e)}**"
        logger.error(f"Error in generate_ethics_response: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return error_msg

def render_file_selector():
    """Render file selector interface"""
    st.markdown(f"📁 {t('select_document', default='Select Document to Chat With')}")
    
    available_pdfs = get_available_pdfs()
    
    if not available_pdfs:
        st.error(t('no_pdfs_available', default='❌ No PDF files are available in the data folder'))
        return None
    
    # Create options for selector
    options = []
    for pdf_file in available_pdfs:
        display_name = EthicsConfig.PDF_DISPLAY_NAMES.get(pdf_file, pdf_file)
        options.append((pdf_file, display_name))
    
    # Add "All Documents" option
    options.append(("ALL_DOCUMENTS", f"📚 {t('all_documents', default='All Documents Combined')}"))
    
    # File selector
    selected_option = st.selectbox(
        t('choose_source', default='Choose your ethics source:'),
        options=options,
        format_func=lambda x: x[1],
        help=t('file_selector_help', default='Select a specific document to focus on, or choose "All Documents" for comprehensive guidance')
    )
    
    if selected_option:
        return selected_option[0]
    return None

def render_ethics_chat_interface():
    """Render the ethics chat interface with file selection"""
    try:
        logger.info("Starting ethics chat interface rendering with file selection")
        
        # File selector
        selected_file = render_file_selector()
        
        if not selected_file:
            st.info(t('please_select_document', default='Please select a document to begin chatting.'))
            return
        
        # Load appropriate document(s) based on selection
        if selected_file == "ALL_DOCUMENTS":
            # Load all documents
            if 'ethics_documents_all' not in st.session_state or st.session_state.ethics_documents_all is None:
                logger.info("Loading all ethics documents")
                with st.spinner(t('loading_all_documents', default='Loading all ethics documents...')):
                    content_dict, metadata_dict, messages = load_multiple_ethics_documents()
                    
                    if content_dict and content_dict.get('combined'):
                        st.session_state.ethics_documents_all = {
                            'content': content_dict['combined'],
                            'metadata': metadata_dict,
                            'source_info': f"All Documents ({len(metadata_dict)} sources)"
                        }
                        
                        # Show status messages
                        for message in messages:
                            if message.startswith('✅'):
                                st.success(message)
                            elif message.startswith('⚠️'):
                                st.warning(message)
                            elif message.startswith('❌'):
                                st.error(message)
                    else:
                        for message in messages:
                            if message.startswith('❌'):
                                st.error(message)
                        return
            
            current_doc = st.session_state.ethics_documents_all
            source_display = f"📚 {t('all_documents', default='All Documents Combined')}"
            
        else:
            # Load single document
            session_key = f'ethics_document_{selected_file}'
            if session_key not in st.session_state or st.session_state[session_key] is None:
                logger.info(f"Loading single document: {selected_file}")
                with st.spinner(f"{t('loading_document', default='Loading document')}: {EthicsConfig.PDF_DISPLAY_NAMES.get(selected_file, selected_file)}..."):
                    content, metadata, message = load_single_ethics_document(selected_file)
                    
                    if content and content.strip():
                        st.session_state[session_key] = {
                            'content': content,
                            'metadata': metadata,
                            'source_info': EthicsConfig.PDF_DISPLAY_NAMES.get(selected_file, selected_file)
                        }
                        st.success(message)
                    else:
                        st.error(f"❌ {message}")
                        return
            
            current_doc = st.session_state[session_key]
            source_display = EthicsConfig.PDF_DISPLAY_NAMES.get(selected_file, selected_file)
        
        # Display current source info
        st.markdown(f"**{t('current_source', default='Current Source')}:** {source_display}")
        
        # Show document info
        with st.expander(f"📖 {t('about_selected_source', default='About Selected Source')}", expanded=False):
            if selected_file == "ALL_DOCUMENTS":
                metadata_dict = current_doc.get('metadata', {})
                st.markdown(f"**{t('total_documents', default='Total Documents')}:** {len(metadata_dict)}")
                
                total_pages = 0
                total_words = 0
                total_size = 0
                
                for filename, metadata in metadata_dict.items():
                    if metadata and not metadata.get('error'):
                        st.markdown(f"""
                        **📄 {filename}**
                        - **{t('pages', default='Pages')}:** {metadata.get('total_pages', 'Unknown')}
                        - **{t('words', default='Words')}:** {metadata.get('word_count', 0):,}
                        - **{t('file_size', default='File Size')}:** {metadata.get('file_size', 0):,} {t('bytes', default='bytes')}
                        """)
                        total_pages += metadata.get('total_pages', 0)
                        total_words += metadata.get('word_count', 0)
                        total_size += metadata.get('file_size', 0)
                
                st.markdown("---")
                st.markdown(f"""
                **{t('combined_totals', default='Combined Totals')}:**
                - **{t('total_pages', default='Total Pages')}:** {total_pages}
                - **{t('total_words', default='Total Words')}:** {total_words:,}
                - **{t('total_size', default='Total Size')}:** {total_size:,} {t('bytes', default='bytes')}
                """)
            else:
                metadata = current_doc.get('metadata', {})
                if metadata and not metadata.get('error'):
                    st.markdown(f"""
                    **{t('document', default='Document')}:** {selected_file}
                    **{t('pages', default='Pages')}:** {metadata.get('total_pages', 'Unknown')}
                    **{t('words', default='Words')}:** {metadata.get('word_count', 0):,}
                    **{t('file_size', default='File Size')}:** {metadata.get('file_size', 0):,} {t('bytes', default='bytes')}
                    """)
        
        # Example questions based on selected source
        with st.expander(f"💡 {t('example_questions', default='Example Questions for This Source')}", expanded=False):
            if selected_file == "ALL_DOCUMENTS":
                st.markdown(f"""
                **{t('comprehensive_questions', default='Comprehensive Questions:')}**
                - "{t('compare_approaches', default='How do Islamic and modern approaches compare on [topic]?')}"
                - "{t('synthesize_guidance', default='What guidance do all sources provide for [situation]?')}"
                - "{t('different_perspectives', default='What different perspectives do these documents offer on [ethical issue]?')}"
                
                **{t('specific_comparisons', default='Specific Comparisons:')}**
                - "{t('business_ethics_comparison', default='How do Islamic ethics and modern frameworks approach business responsibility?')}"
                - "{t('social_justice_perspectives', default='What are the different perspectives on social justice across these sources?')}"
                """)
            elif "Islamic_Ethics" in selected_file:
                st.markdown(f"""
                **{t('islamic_ethics_questions', default='Islamic Ethics Questions:')}**
                - "{t('islamic_principle_question', default='What Islamic principles guide [specific situation]?')}"
                - "{t('quran_hadith_guidance', default='What guidance does this source provide from Quran and Hadith on [topic]?')}"
                - "{t('islamic_business_ethics', default='How does Islamic ethics approach business and financial decisions?')}"
                - "{t('islamic_social_responsibility', default='What does this volume say about social responsibility?')}"
                """)
            elif "reforming_modernity" in selected_file:
                st.markdown(f"""
                **{t('modern_ethics_questions', default='Modern Ethics Questions:')}**
                - "{t('contemporary_approach', default='How does this document approach contemporary ethical challenges?')}"
                - "{t('modernity_reform', default='What reforms to modern thinking does this document suggest?')}"
                - "{t('modern_frameworks', default='What ethical frameworks are discussed for modern society?')}"
                """)
        
        # Initialize chat for this source
        chat_key = f'messages_{selected_file}'
        audio_key = f'audio_responses_{selected_file}'
        
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        if audio_key not in st.session_state:
            st.session_state[audio_key] = {}
        
        # Chat interface
        st.markdown("---")
        st.markdown(f"💬 {t('chat_with_source', default='Chat with Selected Source')}")
        
        # Display chat messages
        for i, message in enumerate(st.session_state[chat_key]):
            if not isinstance(message, dict):
                logger.warning(f"Invalid message format at index {i}: {message}")
                continue
                
            message_key = f"msg_{selected_file}_{i}_{message.get('timestamp', time.time())}"
            
            if message.get("role") == "user":
                st.markdown(f"""
                <div style="background: #e8f4fd; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #1976d2;">
                    <strong>🙋 {t('you', default='You')}:</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
            elif message.get("role") == "assistant":
                st.markdown(f"""
                <div style="background: #f3e5f5; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7b1fa2;">
                    <strong>📋 {t('ethics_advisor', default='Ethics Advisor')} ({source_display}):</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
                
                # Add audio support if enabled
                if st.session_state.get('audio_enabled', True):
                    if message_key not in st.session_state[audio_key]:
                        try:
                            from app import generate_audio_response, create_audio_player
                            with st.spinner(t('generating_audio', default='Generating audio...')):
                                audio_bytes = generate_audio_response(
                                    message.get('content', ''), 
                                    st.session_state.get('selected_voice', 'alloy')
                                )
                                if audio_bytes:
                                    st.session_state[audio_key][message_key] = audio_bytes
                        except Exception as e:
                            logger.error(f"Error generating audio: {e}")
                    
                    # Display audio player if available
                    if message_key in st.session_state[audio_key]:
                        try:
                            from app import create_audio_player
                            audio_html = create_audio_player(
                                st.session_state[audio_key][message_key], 
                                key=message_key
                            )
                            st.markdown(audio_html, unsafe_allow_html=True)
                        except Exception as e:
                            logger.error(f"Error displaying audio player: {e}")
        
        # Chat input
        placeholder_text = t('ask_question_about_source', default=f'Ask a question about {source_display}...')
        if prompt := st.chat_input(placeholder_text):
            try:
                logger.info(f"Processing user input for {selected_file}: {prompt[:100]}...")
                
                # Add user message
                user_message = {
                    "role": "user",
                    "content": prompt,
                    "timestamp": time.time()
                }
                st.session_state[chat_key].append(user_message)
                
                # Immediately display the user message
                st.markdown(f"""
                <div style="background: #e8f4fd; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #1976d2;">
                        <strong>🙋 {t('you', default='You')}:</strong><br>{prompt}
                </div>
                """, unsafe_allow_html=True)
                
                # Generate ethics response
                with st.spinner(f"{t('consulting', default='Consulting')} {source_display}..."):
                    response = generate_ethics_response(
                        prompt,
                        current_doc['content'],
                        current_doc['source_info']
                    )
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": time.time()
                }
                st.session_state[chat_key].append(ai_message)
                
                # Immediately display the AI response
                st.markdown(f"""
                <div style="background: #f3e5f5; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7b1fa2;">
                    <strong>📋 {t('ethics_advisor', default='Ethics Advisor')} ({source_display}):</strong><br>{response}
                </div>
                """, unsafe_allow_html=True)
                
                # Generate and display audio if enabled
                if st.session_state.get('audio_enabled', True):
                    message_key = f"msg_{selected_file}_{len(st.session_state[chat_key])-1}_{ai_message['timestamp']}"
                    try:
                        from app import generate_audio_response, create_audio_player
                        with st.spinner(t('generating_audio', default='Generating audio...')):
                            audio_bytes = generate_audio_response(
                                response, 
                                st.session_state.get('selected_voice', 'alloy')
                            )
                            if audio_bytes:
                                st.session_state[audio_key][message_key] = audio_bytes
                                # Display audio player immediately
                                audio_html = create_audio_player(audio_bytes, key=message_key)
                                st.markdown(audio_html, unsafe_allow_html=True)
                    except Exception as e:
                        logger.error(f"Error generating audio: {e}")
                
                logger.info("Successfully processed user input and generated response")
                
            except Exception as e:
                error_msg = f"❌ **Error processing your question: {str(e)}**"
                st.error(error_msg)
                logger.error(f"Error processing chat input: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Control buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button(f"🔄 {t('new_session', default='New Session')}", type="secondary"):
                st.session_state[chat_key] = []
                st.session_state[audio_key] = {}
                st.rerun()
        
        with col2:
            if st.button(f"🗑️ {t('clear_chat', default='Clear Chat')}", type="secondary"):
                st.session_state[chat_key] = []
                st.session_state[audio_key] = {}
                st.rerun()
        
        with col3:
            if st.button(f"📁 {t('change_source', default='Change Source')}", type="secondary"):
                # Clear current selection to force re-selection
                if 'file_selector_reset' not in st.session_state:
                    st.session_state.file_selector_reset = 0
                st.session_state.file_selector_reset += 1
                st.rerun()
                
    except Exception as e:
        error_msg = f"❌ **Critical error in ethics interface: {str(e)}**"
        st.error(error_msg)
        logger.error(f"Critical error in render_ethics_chat_interface: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Show debug information
        with st.expander("🔧 Debug Information", expanded=True):
            st.code(f"""
            Error: {str(e)}
            Session state keys: {list(st.session_state.keys())}
            Selected file: {locals().get('selected_file', 'Not selected')}
            Available PDFs: {get_available_pdfs()}
            """)

def initialize_ethics_session_state():
    """Initialize ethics-specific session state variables for file selection"""
    try:
        # Initialize containers for different document types
        if 'ethics_documents_all' not in st.session_state:
            st.session_state.ethics_documents_all = None
        
        # Initialize individual document containers
        for pdf_file in EthicsConfig.ETHICS_PDF_FILES:
            session_key = f'ethics_document_{pdf_file}'
            if session_key not in st.session_state:
                st.session_state[session_key] = None
        
        logger.info("Ethics session state initialized successfully for file selection")
    except Exception as e:
        logger.error(f"Error initializing ethics session state: {e}")