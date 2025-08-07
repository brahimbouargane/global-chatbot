# localization.py - Complete working version

import streamlit as st
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Global translations dictionary
TRANSLATIONS = {}

def load_translations():
    """Load translations from JSON files"""
    global TRANSLATIONS
    
    translations_dir = Path("translations")
    
    # Default English fallback
    TRANSLATIONS = {
        'en': {
            'language_selector': 'Language',
            'voice_settings': 'Voice Settings',
            'enable_audio': 'Enable Audio Responses',
            'audio_help': 'Toggle audio responses for accessibility',
            'select_voice': 'Select Voice',
            'voice_help': 'Choose the voice for audio responses',
            'test_voice': 'Test Voice',
            'test_audio_text': 'Hello! This is how I will sound when reading responses to you.',
            'generating_audio': 'Generating audio...',
            'audio_ready': 'Audio ready!',
            'audio_error': 'Failed to generate audio',
            'audio_disabled': 'Audio responses are disabled',
            'audio_response': 'Audio Response',
            'audio_not_supported': 'Your browser does not support audio playback.',
            'system_status': 'System Status',
            'quick_actions': 'Quick Actions',
            'clear_chat': 'Clear Chat',
            'api_key_missing': 'OpenAI API key not configured',
            'ethics_available': 'Ethics System Available',
            'ethics_not_available': 'Ethics System Not Available',
            'ai_connected': 'AI Service Connected',
            'ai_not_connected': 'AI Service Not Available',
            'app_title': 'Ethics Assistant',
            'app_subtitle': 'Your guide to ethical decision-making'
        }
    }
    
    # Load from JSON files if they exist
    if translations_dir.exists():
        for json_file in translations_dir.glob("*.json"):
            lang_code = json_file.stem
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    
                    # Merge with defaults, keeping existing keys
                    if lang_code not in TRANSLATIONS:
                        TRANSLATIONS[lang_code] = {}
                    
                    # Add file data to existing translations
                    TRANSLATIONS[lang_code].update(file_data)
                    
                    # Add missing ethics keys if not present
                    if lang_code == 'ar':
                        arabic_ethics = {
                            'voice_settings': 'إعدادات الصوت',
                            'enable_audio': 'تفعيل الردود الصوتية',
                            'system_status': 'حالة النظام',
                            'quick_actions': 'الإجراءات السريعة',
                            'ethics_available': 'نظام الأخلاقيات متاح',
                            'ai_connected': 'خدمة الذكاء الاصطناعي متصلة',
                            'app_title': 'مساعد الأخلاقيات',
                            'app_subtitle': 'دليلك لاتخاذ القرارات الأخلاقية'
                        }
                        for key, value in arabic_ethics.items():
                            if key not in TRANSLATIONS[lang_code]:
                                TRANSLATIONS[lang_code][key] = value
                    
                    logger.info(f"✅ Loaded {lang_code}: {len(TRANSLATIONS[lang_code])} keys")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {json_file}: {e}")

def get_current_language():
    """Get current language from session state"""
    return st.session_state.get('language', 'en')

def get_language_name(lang_code):
    """Get display name for language"""
    names = {
        'en': 'English',
        'ar': 'العربية',
        'fr': 'Français', 
        'es': 'Español'
    }
    return names.get(lang_code, lang_code)

def t(key, default=None, **kwargs):
    """Translation function"""
    current_lang = get_current_language()
    
    # Try current language first
    if current_lang in TRANSLATIONS and key in TRANSLATIONS[current_lang]:
        text = TRANSLATIONS[current_lang][key]
    # Fallback to English
    elif key in TRANSLATIONS.get('en', {}):
        text = TRANSLATIONS['en'][key]
    # Use default or key
    else:
        text = default if default else key
    
    # Handle parameter substitution
    if kwargs and isinstance(text, str) and '{' in text:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass  # Ignore formatting errors
    
    return str(text)

def init_language_system():
    """Initialize the language system"""
    # Load translations
    load_translations()
    
    # Initialize session state
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
        
    logger.info(f"Language system initialized. Current: {get_current_language()}")

def render_language_selector():
    """Render language selector"""
    language_options = {
        'en': '🇺🇸 English',
        'ar': '🇸🇦 العربية', 
        'fr': '🇫🇷 Français',
        'es': '🇪🇸 Español'
    }
    
    # Only show languages we have translations for
    available_langs = {k: v for k, v in language_options.items() if k in TRANSLATIONS}
    
    if len(available_langs) > 1:
        current_lang = get_current_language()
        
        # Ensure current language is in available options
        if current_lang not in available_langs:
            current_lang = 'en'
            st.session_state.language = 'en'
        
        try:
            current_index = list(available_langs.keys()).index(current_lang)
        except ValueError:
            current_index = 0
        
        selected = st.selectbox(
            t('language_selector', 'Language'),
            options=list(available_langs.keys()),
            format_func=lambda x: available_langs[x],
            index=current_index,
            key="lang_selector"
        )
        
        # Update language if changed
        if selected != st.session_state.get('language'):
            st.session_state.language = selected
            logger.info(f"Language changed to: {selected}")
            st.rerun()
    else:
        st.write("Only English available")

def get_rtl_css():
    """Get RTL CSS for Arabic"""
    if get_current_language() == 'ar':
        return """
   
        """
    return ""

# For backwards compatibility
class LanguageManager:
    def __init__(self):
        pass
    
    @property
    def current_language(self):
        return get_current_language()
    
    def is_rtl(self):
        return get_current_language() == 'ar'
    
    def get_text(self, key, default=None, **kwargs):
        return t(key, default, **kwargs)

# Global instance for backwards compatibility
language_manager = LanguageManager()