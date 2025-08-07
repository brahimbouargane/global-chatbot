# ethics_handler.py - Simplified Version without Authentication

import streamlit as st
import os
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
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
    ETHICS_PDF_FILE = "reforming_modernity.pdf"  # Your ethics PDF file
    DATA_FOLDER = "data"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    MAX_CONTENT_LENGTH = 15000

def read_pdf_directly(file_path: Path) -> Tuple[Optional[str], Dict[str, Any]]:
    """Read PDF file directly using PyPDF2"""
    try:
        from PyPDF2 import PdfReader
        logger.info(f"Reading PDF directly: {file_path}")
        
        reader = PdfReader(str(file_path))
        text = ""
        total_pages = len(reader.pages)
        
        logger.info(f"PDF has {total_pages} pages")
        
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text
                    logger.info(f"Successfully extracted text from page {page_num + 1}")
                else:
                    logger.warning(f"No text found on page {page_num + 1}")
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
        
        logger.info(f"Successfully read PDF. Text length: {len(text)} characters")
        return text, metadata
        
    except Exception as e:
        logger.error(f"Error reading PDF directly: {e}")
        return None, {'error': str(e)}

def load_ethics_document() -> Tuple[Optional[str], Dict[str, Any], str]:
    """Load the ethics document (reforming_modernity.pdf) with better error handling"""
    try:
        pdf_path = Path(EthicsConfig.DATA_FOLDER) / EthicsConfig.ETHICS_PDF_FILE
        
        logger.info(f"Attempting to load ethics document from: {pdf_path}")
        
        if not pdf_path.exists():
            error_msg = f"Ethics document not found: {pdf_path}"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Check if the file is readable
        if not os.access(pdf_path, os.R_OK):
            error_msg = f"Cannot read ethics document: {pdf_path} (permission denied)"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Check file size
        file_size = pdf_path.stat().st_size
        logger.info(f"File size: {file_size} bytes")
        
        if file_size == 0:
            error_msg = f"Ethics document is empty: {pdf_path}"
            logger.error(error_msg)
            return None, {}, error_msg
        
        # Try to read PDF directly first
        logger.info("Attempting to read PDF directly with PyPDF2")
        content, metadata = read_pdf_directly(pdf_path)
        
        if content and content.strip():
            logger.info(f"Successfully loaded ethics document using direct PDF reader")
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Metadata keys: {list(metadata.keys()) if metadata else 'No metadata'}")
            return content, metadata, f"Loaded {EthicsConfig.ETHICS_PDF_FILE} successfully"
        
        # If direct reading failed, try importing from app
        logger.info("Direct PDF reading failed, trying to import from app.py")
        try:
            from app import read_document
            logger.info("Successfully imported read_document function from app")
            content, metadata = read_document(pdf_path)
            
            if content and content.strip():
                logger.info(f"Successfully loaded ethics document using app.read_document")
                return content, metadata, f"Loaded {EthicsConfig.ETHICS_PDF_FILE} successfully"
        except ImportError as e:
            logger.warning(f"Cannot import read_document function: {e}")
        except Exception as e:
            logger.warning(f"Error using app.read_document: {e}")
        
        # If both methods failed
        error_msg = f"Failed to extract content from {EthicsConfig.ETHICS_PDF_FILE}. The PDF might be corrupted, password-protected, or contain only images."
        logger.error(error_msg)
        return None, metadata or {}, error_msg
            
    except Exception as e:
        error_msg = f"Error loading ethics document: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None, {}, error_msg

def generate_ethics_response(question: str, document_content: str) -> str:
    """Generate AI response for ethics-related questions (simplified, no student info needed)"""
    try:
        logger.info("Starting ethics response generation")
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
        
        # Get current language for AI response - DIRECT METHOD
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
        
        # Truncate content if too long
        truncated_content = document_content[:EthicsConfig.MAX_CONTENT_LENGTH]
        logger.info(f"Using content length: {len(truncated_content)} characters")
        logger.info(f"AI will respond in: {current_language}")
        
        system_prompt = f"""You are an expert ethics advisor. You are helping with ethics guidance based on the "Reforming Modernity" document.

LANGUAGE INSTRUCTION: {language_instruction}

ETHICS DOCUMENT CONTENT:
{truncated_content}

INSTRUCTIONS:
- {language_instruction}
- Answer ethics questions based ONLY on the provided "Reforming Modernity" document content
- Provide thoughtful, well-reasoned ethical guidance based on what's actually in the document
- Reference specific sections, concepts, or examples from the document when relevant
- If the document discusses specific ethical frameworks, theories, or principles, use those
- Help people understand and apply the ethical concepts presented in this document
- Encourage critical thinking about ethical issues as presented in the material
- Be supportive and educational in your approach
- If a question cannot be answered from the document content, clearly state this and suggest what topics the document does cover
- Always maintain academic integrity and professional ethics standards

CONTEXT:
- Document: Reforming Modernity (Ethics Material)
- Purpose: Ethics guidance based on this specific document
- Audience: Anyone seeking ethical guidance
- Response language: {current_language}

Remember: Base your responses strictly on the actual content of the "Reforming Modernity" document. If the document focuses on specific ethical themes, theories, or applications, emphasize those in your responses. ALWAYS respond in the requested language."""

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

def render_ethics_chat_interface():
    """Render the ethics chat interface (simplified, no authentication required)"""
    try:
        logger.info("Starting ethics chat interface rendering")
        
        # Load ethics document if not already loaded
        if 'ethics_document' not in st.session_state or st.session_state.ethics_document is None:
            logger.info("Loading ethics document for the first time")
            with st.spinner("Loading ethics guidance materials..."):
                content, metadata, message = load_ethics_document()
                
                if content and content.strip():
                    st.session_state.ethics_document = {
                        'content': content,
                        'metadata': metadata,
                        'filename': EthicsConfig.ETHICS_PDF_FILE
                    }
                    st.success(message)
                    logger.info("Ethics document loaded successfully")
                    
                    # Show document info
                    with st.expander(f"📖 {t('about_this_ethics_document', default='About This Ethics Document')}", expanded=False):
                       st.markdown(f"""
                        **{t('document', default='Document')}:** {EthicsConfig.ETHICS_PDF_FILE}
                        **{t('pages', default='Pages')}:** {metadata.get('total_pages', 'Unknown') if metadata else 'Unknown'}
                        **{t('words', default='Words')}:** {metadata.get('word_count', 0) if metadata else 'Unknown'}
                        **{t('file_size', default='File Size')}:** {metadata.get('file_size', 0) if metadata else 'Unknown'} {t('bytes', default='bytes')}

                        {t('ai_assistant_help_text', default='This AI assistant will help you understand and apply the ethical concepts and guidance contained in this document for professional decision-making.')}
                        """)

                else:
                    st.error(f"❌ **{message}**")
                    st.info(t('ensure_pdf_readable', default="Please ensure 'reforming_modernity.pdf' is in your data folder and is readable."))
                    logger.error(f"Failed to load ethics document: {message}")
                    
                    # Debug information
                    with st.expander(f"🔧 {t('debug_information', default='Debug Information')}", expanded=False):
                        data_folder_path = Path(EthicsConfig.DATA_FOLDER)
                        pdf_file_path = data_folder_path / EthicsConfig.ETHICS_PDF_FILE
                        
                        st.code(f"""
                        Expected file path: {pdf_file_path}
                        File exists: {pdf_file_path.exists()}
                        Data folder exists: {data_folder_path.exists()}
                        Content received: {content is not None}
                        Content length: {len(content) if content else 0}
                        Metadata: {metadata}
                        """)
                    return
        
        # Header for ethics assistance
        st.markdown(f"📋 {t('ethics_guidance_assistant', default='Ethics Guidance Assistant')}")
        st.markdown(f"**{t('document', default='Document')}:** {t('reforming_modernity', default='Reforming Modernity')}")
        
        # General example questions
        with st.expander(f"💡 {t('how_to_use_ethics_assistant', default='How to Use This Ethics Assistant')}", expanded=False):
            st.markdown(f"""
            **{t('you_can_ask_questions_like', default='You can ask questions like:')}**
            - "{t('main_ethical_principles_question', default='What are the main ethical principles discussed in this document?')}"
            - "{t('ethical_behavior_definition', default='How does this document define ethical behavior?')}"
            - "{t('guidance_for_situation', default='What guidance does this provide for [specific situation]?')}"
            - "{t('summarize_ethical_concepts', default='Can you summarize the key ethical concepts covered?')}"
            - "{t('document_says_about_topic', default='What does this document say about [specific ethical topic]?')}"
            - "{t('apply_ethical_principles', default='How should I apply these ethical principles in my work/life?')}"

            **{t('tips', default='Tips:')}**
            - {t('be_specific_guidance', default='Be specific about what ethical guidance you\'re looking for')}
            - {t('ask_about_concepts', default='Ask about concepts, principles, or situations mentioned in the document')}
            - {t('request_examples', default='Request examples or applications of ethical principles')}
            - {t('ask_for_clarification', default='Ask for clarification of complex ethical ideas')}
            """)
        
        # Make chat interface more prominent for clients
        st.markdown("---")
        st.markdown(f"💬 {t('ask_your_ethics_question', default='Ask Your Ethics Question')}")
        st.markdown(f"*{t('get_personalized_guidance', default='Get personalized ethics guidance based on professional principles')}*")

        
        # Initialize messages if not exists
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'audio_responses' not in st.session_state:
            st.session_state.audio_responses = {}
        
        # Chat messages display
        for i, message in enumerate(st.session_state.messages):
            if not isinstance(message, dict):
                logger.warning(f"Invalid message format at index {i}: {message}")
                continue
                
            message_key = f"ethics_msg_{i}_{message.get('timestamp', time.time())}"
            
            if message.get("role") == "user":
                st.markdown(f"""
                <div style="background: #e8f4fd; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #1976d2;">
                    <strong>🙋 {t('you', default='You')}:</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
            elif message.get("role") == "assistant":
                st.markdown(f"""
                <div style="background: #f3e5f5; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7b1fa2;">
                    <strong>📋 {t('ethics_advisor', default='Ethics Advisor')}:</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
                
                # Add audio support if enabled
                if st.session_state.get('audio_enabled', True):
                    if message_key not in st.session_state.audio_responses:
                        try:
                            from app import generate_audio_response, create_audio_player
                            with st.spinner(t('generating_audio', default='Generating audio...')):
                                audio_bytes = generate_audio_response(
                                    message.get('content', ''), 
                                    st.session_state.get('selected_voice', 'alloy')
                                )
                                if audio_bytes:
                                    st.session_state.audio_responses[message_key] = audio_bytes
                        except Exception as e:
                            logger.error(f"Error generating audio: {e}")
                    
                    # Display audio player if available
                    if message_key in st.session_state.audio_responses:
                        try:
                            from app import create_audio_player
                            audio_html = create_audio_player(
                                st.session_state.audio_responses[message_key], 
                                key=message_key
                            )
                            st.markdown(audio_html, unsafe_allow_html=True)
                        except Exception as e:
                            logger.error(f"Error displaying audio player: {e}")
        
        # Chat input
        if prompt := st.chat_input(t('ethics_question_placeholder', default="Ask your ethics question here... (e.g., 'How should I handle this ethical dilemma?')")):
            try:
                logger.info(f"Processing user input: {prompt[:100]}...")
                
                # Add user message
                user_message = {
                    "role": "user",
                    "content": prompt,
                    "timestamp": time.time()
                }
                st.session_state.messages.append(user_message)
                
                # Immediately display the user message
                st.markdown(f"""
                <div style="background: #e8f4fd; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #1976d2;">
                        <strong>🙋 {t('you', default='You')}:</strong><br>{prompt}
                </div>
                """, unsafe_allow_html=True)
                
                # Generate ethics response
                with st.spinner(t('consulting_ethics', default='Consulting ethics guidance...')):
                    ethics_doc = st.session_state.get('ethics_document')
                    if not ethics_doc or not ethics_doc.get('content'):
                        st.error(t('ethics_document_not_loaded', default='❌ **Ethics document not properly loaded**'))
                        return
                    
                    response = generate_ethics_response(
                        prompt,
                        ethics_doc['content']
                    )
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": time.time()
                }
                st.session_state.messages.append(ai_message)
                
                # Immediately display the AI response
                st.markdown(f"""
                <div style="background: #f3e5f5; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7b1fa2;">
                    <strong>📋 {t('ethics_advisor', default='Ethics Advisor')}:</strong><br>{response}
                </div>
                """, unsafe_allow_html=True)
                
                # Generate and display audio if enabled
                if st.session_state.get('audio_enabled', True):
                    message_key = f"ethics_msg_{len(st.session_state.messages)-1}_{ai_message['timestamp']}"
                    try:
                        from app import generate_audio_response, create_audio_player
                        with st.spinner(t('generating_audio', default='Generating audio...')):
                            audio_bytes = generate_audio_response(
                                response, 
                                st.session_state.get('selected_voice', 'alloy')
                            )
                            if audio_bytes:
                                st.session_state.audio_responses[message_key] = audio_bytes
                                # Display audio player immediately
                                audio_html = create_audio_player(audio_bytes, key=message_key)
                                st.markdown(audio_html, unsafe_allow_html=True)
                    except Exception as e:
                        logger.error(f"Error generating audio: {e}")
                
                logger.info("Successfully processed user input and generated response")
                # Don't rerun here - let the display happen naturally
                
            except Exception as e:
                error_msg = f"❌ **Error processing your question: {str(e)}**"
                st.error(error_msg)
                logger.error(f"Error processing chat input: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Control buttons
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button(f"🔄 {t('new_session', default='New Session')}", type="secondary"):
                st.session_state.messages = []
                st.session_state.audio_responses = {}
                st.rerun()
        
        with col2:
            if st.button(f"🗑️ {t('clear_chat', default='Clear Chat')}", type="secondary"):
                st.session_state.messages = []
                st.session_state.audio_responses = {}
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
            Ethics document: {getattr(st.session_state, 'ethics_document', 'Not set')}
            """)

def initialize_ethics_session_state():
    """Initialize ethics-specific session state variables"""
    try:
        if 'ethics_document' not in st.session_state:
            st.session_state.ethics_document = None
        logger.info("Ethics session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing ethics session state: {e}")