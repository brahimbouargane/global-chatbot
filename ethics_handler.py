# ethics_handler.py - Debug Version with Better Error Handling

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

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

class EthicsConfig:
    """Configuration for ethics document handling"""
    ETHICS_PDF_FILE = "reforming_modernity.pdf"  # Your ethics PDF file
    DATA_FOLDER = "data"
    MAX_TOKENS = 1500
    TEMPERATURE = 0.3
    MODEL = "gpt-3.5-turbo"
    MAX_CONTENT_LENGTH = 15000

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
        
        # Import the document reading functions from your main app
        try:
            from app import read_document
            logger.info("Successfully imported read_document function")
        except ImportError as e:
            error_msg = f"Cannot import read_document function: {e}"
            logger.error(error_msg)
            return None, {}, error_msg
        
        logger.info(f"Reading document: {pdf_path}")
        content, metadata = read_document(pdf_path)
        
        if content and content.strip():
            logger.info(f"Successfully loaded ethics document: {EthicsConfig.ETHICS_PDF_FILE}")
            logger.info(f"Content length: {len(content)} characters")
            logger.info(f"Metadata keys: {list(metadata.keys()) if metadata else 'No metadata'}")
            return content, metadata, f"Loaded {EthicsConfig.ETHICS_PDF_FILE} successfully"
        else:
            error_msg = f"Failed to extract content from {EthicsConfig.ETHICS_PDF_FILE}"
            logger.error(error_msg)
            logger.error(f"Content: {content}")
            logger.error(f"Metadata: {metadata}")
            return None, metadata or {}, error_msg
            
    except Exception as e:
        error_msg = f"Error loading ethics document: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None, {}, error_msg

def generate_ethics_response(question: str, document_content: str, student_info: Dict) -> str:
    """Generate AI response for ethics-related questions with better error handling"""
    try:
        logger.info("Starting ethics response generation")
        logger.info(f"Question length: {len(question) if question else 'None'}")
        logger.info(f"Document content length: {len(document_content) if document_content else 'None'}")
        logger.info(f"Student info keys: {list(student_info.keys()) if student_info else 'None'}")
        
        if not client:
            error_msg = f"🔑 **{t('api_key_missing', default='OpenAI API key not configured')}**"
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
        
        # Safely get student info with defaults
        student_id = student_info.get('student_id', 'Unknown') if student_info else 'Unknown'
        programme = student_info.get('programme', 'Unknown') if student_info else 'Unknown'
        
        logger.info(f"Student ID: {student_id}, Programme: {programme}")
        
        # Truncate content if too long
        truncated_content = document_content[:EthicsConfig.MAX_CONTENT_LENGTH]
        logger.info(f"Using content length: {len(truncated_content)} characters")
        
        system_prompt = f"""You are an expert ethics advisor for University of Roehampton students. You are helping with ethics guidance based on the "Reforming Modernity" document.

STUDENT INFORMATION:
- Student ID: {student_id}
- Programme: {programme}

ETHICS DOCUMENT CONTENT:
{truncated_content}

INSTRUCTIONS:
- Answer ethics questions based ONLY on the provided "Reforming Modernity" document content
- Provide thoughtful, well-reasoned ethical guidance based on what's actually in the document
- Reference specific sections, concepts, or examples from the document when relevant
- If the document discusses specific ethical frameworks, theories, or principles, use those
- Help students understand and apply the ethical concepts presented in this document
- Encourage critical thinking about ethical issues as presented in the material
- Be supportive and educational in your approach
- If a question cannot be answered from the document content, clearly state this and suggest what topics the document does cover
- Always maintain academic integrity and professional ethics standards

CONTEXT:
- Document: Reforming Modernity (University Ethics Material)
- Purpose: Ethics guidance based on this specific document
- Audience: Roehampton University student

Remember: Base your responses strictly on the actual content of the "Reforming Modernity" document. If the document focuses on specific ethical themes, theories, or applications, emphasize those in your responses."""

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
    """Render the ethics chat interface with comprehensive error handling"""
    try:
        logger.info("Starting ethics chat interface rendering")
        
        # Check session state integrity
        if not hasattr(st.session_state, 'student_id') or st.session_state.student_id is None:
            st.error("❌ **Student authentication required**")
            logger.error("Student ID not found in session state")
            if st.button("🔙 Back to Welcome"):
                st.session_state.conversation_step = 'welcome'
                st.rerun()
            return
        
        if not hasattr(st.session_state, 'student_data') or st.session_state.student_data is None:
            st.error("❌ **Student data not loaded**")
            logger.error("Student data not found in session state")
            if st.button("🔙 Back to Welcome"):
                st.session_state.conversation_step = 'welcome'
                st.rerun()
            return
        
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
                    with st.expander("📖 About This Ethics Document", expanded=False):
                        st.markdown(f"""
                        **Document:** {EthicsConfig.ETHICS_PDF_FILE}
                        **Pages:** {metadata.get('total_pages', 'Unknown') if metadata else 'Unknown'}
                        **Words:** {metadata.get('word_count', 0) if metadata else 'Unknown'}
                        **File Size:** {metadata.get('file_size', 0) if metadata else 'Unknown'} bytes
                        
                        This AI assistant will help you understand and apply the ethical concepts and guidance contained in this document.
                        """)
                else:
                    st.error(f"❌ **{message}**")
                    st.info("Please ensure 'reforming_modernity.pdf' is in your data folder and is readable.")
                    logger.error(f"Failed to load ethics document: {message}")
                    
                    # Debug information
                    with st.expander("🔧 Debug Information", expanded=False):
                        st.code(f"""
                        Expected file path: {Path(EthicsConfig.DATA_FOLDER) / EthicsConfig.ETHICS_PDF_FILE}
                        File exists: {Path(EthicsConfig.DATA_FOLDER / EthicsConfig.ETHICS_PDF_FILE).exists()}
                        Data folder exists: {Path(EthicsConfig.DATA_FOLDER).exists()}
                        Content received: {content is not None}
                        Content length: {len(content) if content else 0}
                        Metadata: {metadata}
                        """)
                    
                    if st.button("🔙 Back to Welcome"):
                        st.session_state.conversation_step = 'welcome'
                        st.rerun()
                    return
        
        # Header for ethics assistance
        st.markdown(f"### 📋 Ethics Guidance")
        st.markdown(f"**Student:** {st.session_state.student_id}")
        
        # Safely access student data
        programme = "Unknown"
        if st.session_state.student_data and isinstance(st.session_state.student_data, dict):
            programme = st.session_state.student_data.get('programme', 'Unknown')
        
        st.markdown(f"**Programme:** {programme}")
        st.markdown(f"**Document:** Reforming Modernity")
        
        # General example questions
        with st.expander("💡 How to Use This Ethics Assistant", expanded=False):
            st.markdown("""
            **You can ask questions like:**
            - "What are the main ethical principles discussed in this document?"
            - "How does this document define ethical behavior?"
            - "What guidance does this provide for [specific situation]?"
            - "Can you summarize the key ethical concepts covered?"
            - "What does this document say about [specific ethical topic]?"
            - "How should I apply these ethical principles in my studies/work?"
            
            **Tips:**
            - Be specific about what ethical guidance you're looking for
            - Ask about concepts, principles, or situations mentioned in the document
            - Request examples or applications of ethical principles
            - Ask for clarification of complex ethical ideas
            """)
        
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
                    <strong>🙋 You:</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
            elif message.get("role") == "assistant":
                st.markdown(f"""
                <div style="background: #f3e5f5; color: #000; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #7b1fa2;">
                    <strong>📋 Ethics Advisor:</strong><br>{message.get('content', '')}
                </div>
                """, unsafe_allow_html=True)
                
                # Add audio support if enabled
                if st.session_state.get('audio_enabled', True):
                    if message_key not in st.session_state.audio_responses:
                        try:
                            from app import generate_audio_response, create_audio_player
                            with st.spinner('Generating audio...'):
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
        if prompt := st.chat_input("Ask me about ethics based on the Reforming Modernity document..."):
            try:
                logger.info(f"Processing user input: {prompt[:100]}...")
                
                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt,
                    "timestamp": time.time()
                })
                
                # Generate ethics response
                with st.spinner("Consulting ethics guidance..."):
                    student_info = {
                        'student_id': st.session_state.student_id,
                        'programme': programme
                    }
                    
                    ethics_doc = st.session_state.get('ethics_document')
                    if not ethics_doc or not ethics_doc.get('content'):
                        st.error("❌ **Ethics document not properly loaded**")
                        return
                    
                    response = generate_ethics_response(
                        prompt,
                        ethics_doc['content'],
                        student_info
                    )
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": time.time()
                }
                st.session_state.messages.append(ai_message)
                
                logger.info("Successfully processed user input and generated response")
                st.rerun()
                
            except Exception as e:
                error_msg = f"❌ **Error processing your question: {str(e)}**"
                st.error(error_msg)
                logger.error(f"Error processing chat input: {str(e)}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Control buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 New Session", type="secondary"):
                try:
                    from app import reset_conversation
                    reset_conversation()
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error resetting conversation: {e}")
                    st.session_state.conversation_step = 'welcome'
                    st.rerun()
        
        with col2:
            if st.button("🔙 Back to Menu", type="secondary"):
                st.session_state.conversation_step = 'welcome'
                st.session_state.messages = []
                st.session_state.audio_responses = {}
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear Chat", type="secondary"):
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
            Student ID: {getattr(st.session_state, 'student_id', 'Not set')}
            Student data type: {type(getattr(st.session_state, 'student_data', None))}
            Ethics document: {getattr(st.session_state, 'ethics_document', 'Not set')}
            """)
        
        if st.button("🔙 Back to Welcome"):
            st.session_state.conversation_step = 'welcome'
            st.rerun()

def initialize_ethics_session_state():
    """Initialize ethics-specific session state variables"""
    try:
        if 'ethics_document' not in st.session_state:
            st.session_state.ethics_document = None
        logger.info("Ethics session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing ethics session state: {e}")