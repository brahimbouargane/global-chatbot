# localization.py - Language Management System

import json
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st

class LanguageManager:
    """Centralized language management system with best practices"""
    
    def __init__(self):
        self.current_language = 'en'
        self.translations = {}
        self.rtl_languages = {'ar'}  # Right-to-left languages
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        translations_dir = Path("translations")
        translations_dir.mkdir(exist_ok=True)
        
        # Default translations if files don't exist
        self.translations = {
            'en': self._get_english_translations(),
            'ar': self._get_arabic_translations(),
            'fr': self._get_french_translations(),
            'es': self._get_spanish_translations()
        }
        
        # Try to load from files
        for lang_code in self.translations.keys():
            file_path = translations_dir / f"{lang_code}.json"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading {lang_code}.json: {e}")
    
    def save_translations(self):
        """Save translations to JSON files"""
        translations_dir = Path("translations")
        translations_dir.mkdir(exist_ok=True)
        
        for lang_code, translations in self.translations.items():
            file_path = translations_dir / f"{lang_code}.json"
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving {lang_code}.json: {e}")
    
    def set_language(self, lang_code: str):
        """Set current language"""
        if lang_code in self.translations:
            self.current_language = lang_code
            # Update session state
            if 'language' not in st.session_state or st.session_state.language != lang_code:
                st.session_state.language = lang_code
                st.rerun()
    
    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text with parameter substitution"""
        text = self.translations.get(self.current_language, {}).get(key, key)
        
        # Fallback to English if translation missing
        if text == key and self.current_language != 'en':
            text = self.translations.get('en', {}).get(key, key)
        
        # Parameter substitution
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass  # Ignore missing parameters
        
        return text
    
    def is_rtl(self) -> bool:
        """Check if current language is right-to-left"""
        return self.current_language in self.rtl_languages
    
    def get_language_options(self) -> Dict[str, str]:
        """Get available language options for UI"""
        return {
            'en': '🇺🇸 English',
            'ar': '🇸🇦 العربية',
            'fr': '🇫🇷 Français',
            'es': '🇪🇸 Español'
        }
    
    def _get_english_translations(self) -> Dict[str, str]:
        """English translations (base language)"""
        return {
            # App Headers
            'app_title': 'AI Multi-Document Assistant',
            'app_subtitle': 'Search across multiple documents simultaneously',
            'powered_by': 'Powered by AI',
            
            # Navigation & Controls
            'document_library': 'Document Library',
            'controls': 'Controls',
            'clear_chat': 'Clear Chat History',
            'reload_docs': 'Reload Documents',
            'language_selector': 'Language',
            
            # Document Status
            'docs_loaded': '{count} documents loaded',
            'no_docs_loaded': 'No documents loaded',
            'loading_docs': 'Loading documents...',
            'total_files': 'Total Files',
            'total_words': 'Total Words',
            'total_pages': 'Total Pages',
            'total_size': 'Total Size',
            'reading_time': 'Reading Time',
            'minutes': 'min',
            'document_details': 'Document Details',
            
            # File Types
            'file_type': 'Type',
            'words': 'Words',
            'size': 'Size',
            
            # Chat Interface
            'ready_to_search': 'Ready to search across {count} documents!',
            'search_through': 'I can search through: {docs}',
            'and_more': 'and more',
            'try_asking': 'Try asking:',
            'search_placeholder': 'Search across all documents...',
            'enter_question': 'Please enter a question.',
            'searching': 'Searching across all documents...',
            
            # Example Questions
            'example_1': 'What are the main topics covered in the documents?',
            'example_2': 'Find information about [specific topic]',
            'example_3': 'Compare the content between documents',
            'example_4': 'Summarize key points from all documents',
            
            # AI Responses
            'ai_assistant': 'AI Assistant',
            'you': 'You',
            'hello_response': '''👋 Hello! Welcome to **{app_name}**!

I'm your AI assistant with access to **{doc_count} documents** in your library: {doc_list}.

I can help you:
• **Search across all documents** to find relevant information
• **Compare information** between different documents  
• **Summarize content** from one or multiple sources
• **Answer specific questions** with source attribution

What would you like to explore across your document collection?''',
            
            # Error Messages
            'api_key_missing': 'OpenAI client not initialized. Please check your API key.',
            'no_docs_error': 'No documents loaded. Please check your data folder.',
            'rate_limit_error': 'Rate limit reached. Please wait a moment before asking another question.',
            'auth_error': 'Authentication error. Please check your OpenAI API key.',
            'invalid_request': 'Invalid request: {error}',
            'response_error': 'Error generating response: {error}',
            'app_error': 'Application Error: {error}',
            'refresh_page': 'Please refresh the page and try again.',
            
            # Setup Messages
            'api_key_not_found': 'OpenAI API key not found!',
            'add_api_key': 'Please add your OpenAI API key to the .env file:',
            'looking_for_files': 'Looking for PDF and DOCX files in: {folder}',
            'supported_formats': 'Supported formats: PDF, DOCX',
            
            # File Operations
            'looking_in': 'Looking in: {folder}',
            'data_folder_not_found': 'Data folder not found: {folder}',
            'no_supported_docs': 'No supported documents found in {folder}. Found files: {files}',
            'loaded_docs_status': 'Loaded {success}/{total} documents. {failed} failed.',
            'all_docs_loaded': 'Successfully loaded {success}/{total} documents',
            'failed_to_load': 'Failed to load any documents. Errors: {errors}',
        }
    
    def _get_arabic_translations(self) -> Dict[str, str]:
        """Arabic translations"""
        return {
            # App Headers
            'app_title': 'مساعد الذكي متعدد المستندات',
            'app_subtitle': 'البحث عبر مستندات متعددة في آن واحد',
            'powered_by': 'مدعوم بالذكاء الاصطناعي',
            
            # Navigation & Controls
            'document_library': 'مكتبة المستندات',
            'controls': 'عناصر التحكم',
            'clear_chat': 'مسح سجل المحادثة',
            'reload_docs': 'إعادة تحميل المستندات',
            'language_selector': 'اللغة',
            
            # Document Status
            'docs_loaded': 'تم تحميل {count} مستند',
            'no_docs_loaded': 'لم يتم تحميل أي مستندات',
            'loading_docs': 'جاري تحميل المستندات...',
            'total_files': 'إجمالي الملفات',
            'total_words': 'إجمالي الكلمات',
            'total_pages': 'إجمالي الصفحات',
            'total_size': 'الحجم الإجمالي',
            'reading_time': 'وقت القراءة',
            'minutes': 'دقيقة',
            'document_details': 'تفاصيل المستندات',
            
            # File Types
            'file_type': 'النوع',
            'words': 'كلمات',
            'size': 'الحجم',
            
            # Chat Interface
            'ready_to_search': 'جاهز للبحث عبر {count} مستند!',
            'search_through': 'يمكنني البحث من خلال: {docs}',
            'and_more': 'والمزيد',
            'try_asking': 'جرب أن تسأل:',
            'search_placeholder': 'ابحث عبر جميع المستندات...',
            'enter_question': 'يرجى إدخال سؤال.',
            'searching': 'البحث عبر جميع المستندات...',
            
            # Example Questions
            'example_1': 'ما هي الموضوعات الرئيسية المغطاة في المستندات؟',
            'example_2': 'ابحث عن معلومات حول [موضوع محدد]',
            'example_3': 'قارن المحتوى بين المستندات',
            'example_4': 'لخص النقاط الرئيسية من جميع المستندات',
            
            # AI Responses
            'ai_assistant': 'المساعد الذكي',
            'you': 'أنت',
            'hello_response': '''👋 أهلاً! مرحباً بك في **{app_name}**!

أنا مساعدك الذكي مع الوصول إلى **{doc_count} مستند** في مكتبتك: {doc_list}.

يمكنني مساعدتك في:
• **البحث عبر جميع المستندات** للعثور على المعلومات ذات الصلة
• **مقارنة المعلومات** بين المستندات المختلفة
• **تلخيص المحتوى** من مصدر واحد أو مصادر متعددة
• **الإجابة على أسئلة محددة** مع إسناد المصادر

ما الذي تود استكشافه في مجموعة مستنداتك؟''',
            
            # Error Messages
            'api_key_missing': 'لم يتم تهيئة عميل OpenAI. يرجى التحقق من مفتاح API.',
            'no_docs_error': 'لم يتم تحميل أي مستندات. يرجى التحقق من مجلد البيانات.',
            'rate_limit_error': 'تم الوصول إلى حد المعدل. يرجى الانتظار قليلاً قبل طرح سؤال آخر.',
            'auth_error': 'خطأ في المصادقة. يرجى التحقق من مفتاح OpenAI API.',
            'invalid_request': 'طلب غير صحيح: {error}',
            'response_error': 'خطأ في إنتاج الاستجابة: {error}',
            'app_error': 'خطأ في التطبيق: {error}',
            'refresh_page': 'يرجى تحديث الصفحة والمحاولة مرة أخرى.',
            
            # Setup Messages
            'api_key_not_found': 'مفتاح OpenAI API غير موجود!',
            'add_api_key': 'يرجى إضافة مفتاح OpenAI API إلى ملف .env:',
            'looking_for_files': 'البحث عن ملفات PDF و DOCX في: {folder}',
            'supported_formats': 'التنسيقات المدعومة: PDF، DOCX',
            
            # File Operations
            'looking_in': 'البحث في: {folder}',
            'data_folder_not_found': 'مجلد البيانات غير موجود: {folder}',
            'no_supported_docs': 'لا توجد مستندات مدعومة في {folder}. الملفات الموجودة: {files}',
            'loaded_docs_status': 'تم تحميل {success}/{total} مستندات. فشل {failed}.',
            'all_docs_loaded': 'تم تحميل {success}/{total} مستندات بنجاح',
            'failed_to_load': 'فشل في تحميل أي مستندات. الأخطاء: {errors}',
        }
    
    def _get_french_translations(self) -> Dict[str, str]:
        """French translations"""
        return {
            # App Headers
            'app_title': 'Assistant IA Multi-Documents',
            'app_subtitle': 'Recherchez simultanément dans plusieurs documents',
            'powered_by': 'Alimenté par IA',
            
            # Navigation & Controls
            'document_library': 'Bibliothèque de Documents',
            'controls': 'Contrôles',
            'clear_chat': 'Effacer l\'Historique',
            'reload_docs': 'Recharger les Documents',
            'language_selector': 'Langue',
            
            # Document Status
            'docs_loaded': '{count} documents chargés',
            'no_docs_loaded': 'Aucun document chargé',
            'loading_docs': 'Chargement des documents...',
            'total_files': 'Fichiers Totaux',
            'total_words': 'Mots Totaux',
            'total_pages': 'Pages Totales',
            'total_size': 'Taille Totale',
            'reading_time': 'Temps de Lecture',
            'minutes': 'min',
            'document_details': 'Détails des Documents',
            
            # File Types
            'file_type': 'Type',
            'words': 'Mots',
            'size': 'Taille',
            
            # Chat Interface
            'ready_to_search': 'Prêt à rechercher dans {count} documents !',
            'search_through': 'Je peux rechercher dans : {docs}',
            'and_more': 'et plus',
            'try_asking': 'Essayez de demander :',
            'search_placeholder': 'Rechercher dans tous les documents...',
            'enter_question': 'Veuillez entrer une question.',
            'searching': 'Recherche dans tous les documents...',
            
            # Example Questions
            'example_1': 'Quels sont les principaux sujets couverts dans les documents ?',
            'example_2': 'Trouvez des informations sur [sujet spécifique]',
            'example_3': 'Comparez le contenu entre les documents',
            'example_4': 'Résumez les points clés de tous les documents',
            
            # AI Responses
            'ai_assistant': 'Assistant IA',
            'you': 'Vous',
            'hello_response': '''👋 Bonjour ! Bienvenue dans **{app_name}** !

Je suis votre assistant IA avec accès à **{doc_count} documents** dans votre bibliothèque : {doc_list}.

Je peux vous aider à :
• **Rechercher dans tous les documents** pour trouver des informations pertinentes
• **Comparer les informations** entre différents documents
• **Résumer le contenu** d'une ou plusieurs sources
• **Répondre à des questions spécifiques** avec attribution des sources

Que souhaitez-vous explorer dans votre collection de documents ?''',
            
            # Error Messages
            'api_key_missing': 'Client OpenAI non initialisé. Veuillez vérifier votre clé API.',
            'no_docs_error': 'Aucun document chargé. Veuillez vérifier votre dossier de données.',
            'rate_limit_error': 'Limite de taux atteinte. Veuillez attendre un moment avant de poser une autre question.',
            'auth_error': 'Erreur d\'authentification. Veuillez vérifier votre clé API OpenAI.',
            'invalid_request': 'Demande invalide : {error}',
            'response_error': 'Erreur lors de la génération de la réponse : {error}',
            'app_error': 'Erreur d\'Application : {error}',
            'refresh_page': 'Veuillez actualiser la page et réessayer.',
            
            # Setup Messages
            'api_key_not_found': 'Clé API OpenAI non trouvée !',
            'add_api_key': 'Veuillez ajouter votre clé API OpenAI au fichier .env :',
            'looking_for_files': 'Recherche de fichiers PDF et DOCX dans : {folder}',
            'supported_formats': 'Formats supportés : PDF, DOCX',
            
            # File Operations
            'looking_in': 'Recherche dans : {folder}',
            'data_folder_not_found': 'Dossier de données non trouvé : {folder}',
            'no_supported_docs': 'Aucun document supporté trouvé dans {folder}. Fichiers trouvés : {files}',
            'loaded_docs_status': '{success}/{total} documents chargés. {failed} échoués.',
            'all_docs_loaded': '{success}/{total} documents chargés avec succès',
            'failed_to_load': 'Échec du chargement de tous les documents. Erreurs : {errors}',
        }
    
    def _get_spanish_translations(self) -> Dict[str, str]:
        """Spanish translations"""
        return {
            # App Headers
            'app_title': 'Asistente IA Multi-Documentos',
            'app_subtitle': 'Busca en múltiples documentos simultáneamente',
            'powered_by': 'Impulsado por IA',
            
            # Navigation & Controls
            'document_library': 'Biblioteca de Documentos',
            'controls': 'Controles',
            'clear_chat': 'Limpiar Historial',
            'reload_docs': 'Recargar Documentos',
            'language_selector': 'Idioma',
            
            # Document Status
            'docs_loaded': '{count} documentos cargados',
            'no_docs_loaded': 'No hay documentos cargados',
            'loading_docs': 'Cargando documentos...',
            'total_files': 'Archivos Totales',
            'total_words': 'Palabras Totales',
            'total_pages': 'Páginas Totales',
            'total_size': 'Tamaño Total',
            'reading_time': 'Tiempo de Lectura',
            'minutes': 'min',
            'document_details': 'Detalles de Documentos',
            
            # File Types
            'file_type': 'Tipo',
            'words': 'Palabras',
            'size': 'Tamaño',
            
            # Chat Interface
            'ready_to_search': '¡Listo para buscar en {count} documentos!',
            'search_through': 'Puedo buscar en: {docs}',
            'and_more': 'y más',
            'try_asking': 'Intenta preguntar:',
            'search_placeholder': 'Buscar en todos los documentos...',
            'enter_question': 'Por favor ingresa una pregunta.',
            'searching': 'Buscando en todos los documentos...',
            
            # Example Questions
            'example_1': '¿Cuáles son los temas principales cubiertos en los documentos?',
            'example_2': 'Encuentra información sobre [tema específico]',
            'example_3': 'Compara el contenido entre documentos',
            'example_4': 'Resume los puntos clave de todos los documentos',
            
            # AI Responses
            'ai_assistant': 'Asistente IA',
            'you': 'Tú',
            'hello_response': '''👋 ¡Hola! ¡Bienvenido a **{app_name}**!

Soy tu asistente IA con acceso a **{doc_count} documentos** en tu biblioteca: {doc_list}.

Puedo ayudarte a:
• **Buscar en todos los documentos** para encontrar información relevante
• **Comparar información** entre diferentes documentos
• **Resumir contenido** de una o múltiples fuentes
• **Responder preguntas específicas** con atribución de fuentes

¿Qué te gustaría explorar en tu colección de documentos?''',
            
            # Error Messages
            'api_key_missing': 'Cliente OpenAI no inicializado. Por favor verifica tu clave API.',
            'no_docs_error': 'No hay documentos cargados. Por favor verifica tu carpeta de datos.',
            'rate_limit_error': 'Límite de velocidad alcanzado. Por favor espera un momento antes de hacer otra pregunta.',
            'auth_error': 'Error de autenticación. Por favor verifica tu clave API de OpenAI.',
            'invalid_request': 'Solicitud inválida: {error}',
            'response_error': 'Error generando respuesta: {error}',
            'app_error': 'Error de Aplicación: {error}',
            'refresh_page': 'Por favor actualiza la página e intenta de nuevo.',
            
            # Setup Messages
            'api_key_not_found': '¡Clave API de OpenAI no encontrada!',
            'add_api_key': 'Por favor agrega tu clave API de OpenAI al archivo .env:',
            'looking_for_files': 'Buscando archivos PDF y DOCX en: {folder}',
            'supported_formats': 'Formatos soportados: PDF, DOCX',
            
            # File Operations
            'looking_in': 'Buscando en: {folder}',
            'data_folder_not_found': 'Carpeta de datos no encontrada: {folder}',
            'no_supported_docs': 'No se encontraron documentos soportados en {folder}. Archivos encontrados: {files}',
            'loaded_docs_status': '{success}/{total} documentos cargados. {failed} fallaron.',
            'all_docs_loaded': '{success}/{total} documentos cargados exitosamente',
            'failed_to_load': 'Falló la carga de todos los documentos. Errores: {errors}',
        }

# Create global language manager instance
language_manager = LanguageManager()

def t(key: str, **kwargs) -> str:
    """Convenient translation function"""
    return language_manager.get_text(key, **kwargs)

def init_language_system():
    """Initialize language system in session state"""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    language_manager.current_language = st.session_state.language
    
    # Save translations to files on first run
    try:
        language_manager.save_translations()
    except Exception as e:
        print(f"Could not save translation files: {e}")

def render_language_selector():
    """Render language selector in sidebar"""
    languages = language_manager.get_language_options()
    
    selected_language = st.selectbox(
        t('language_selector'),
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(st.session_state.language),
        key="language_selector"
    )
    
    if selected_language != st.session_state.language:
        language_manager.set_language(selected_language)

def get_rtl_css() -> str:
    """Generate RTL CSS if needed"""
    if language_manager.is_rtl():
        return """
      
        """
    return ""

def get_language_specific_ai_prompt(documents_info: str, combined_content: str) -> str:
    """Generate language-specific AI prompt"""
    current_lang = language_manager.current_language
    
    if current_lang == 'ar':
        return f"""أنت محلل مستندات خبير مع إمكانية الوصول إلى مستندات متعددة. مهمتك هي البحث عبر جميع المستندات المقدمة وتقديم إجابات شاملة باللغة العربية.

المستندات المتاحة:
{documents_info}

محتوى المستندات:
{combined_content}

التعليمات:
- ابحث عبر جميع المستندات للعثور على المعلومات ذات الصلة
- اذكر دائماً أي مستند يحتوي على المعلومات باستخدام التنسيق: **[المصدر: اسم_المستند]**
- إذا ظهرت المعلومات في مستندات متعددة، اذكر جميع المصادر ذات الصلة
- استخدم تنسيق markdown لسهولة القراءة
- إذا لم يتم العثور على المعلومات في أي مستند، اذكر ذلك بوضوح
- أعط الأولوية للمعلومات الأكثر صلة وشمولية
- عند المقارنة أو التباين، انسب المعلومات بوضوح إلى مستندات محددة
- كن محادثياً ولكن مهنياً

تنسيق الاستجابة:
- ابدأ بإجابة مباشرة على السؤال
- قم بتضمين إسناد المصدر: **[المصدر: اسم_الملف]**
- أضف تفاصيل ذات صلة مع المصادر
- إذا كانت مستندات متعددة ذات صلة، نظم حسب المصدر أو الموضوع

تذكر: اذكر دائماً مصادرك واستخدم فقط المعلومات من المستندات المقدمة."""
    
    elif current_lang == 'fr':
        return f"""Vous êtes un analyste de documents expert avec accès à plusieurs documents. Votre tâche est de rechercher dans tous les documents fournis et de fournir des réponses complètes en français.

DOCUMENTS DISPONIBLES :
{documents_info}

CONTENU DES DOCUMENTS :
{combined_content}

INSTRUCTIONS :
- Recherchez dans TOUS les documents pour trouver des informations pertinentes
- Indiquez TOUJOURS quel(s) document(s) contiennent les informations en utilisant le format : **[Source : nom_document]**
- Si les informations apparaissent dans plusieurs documents, mentionnez toutes les sources pertinentes
- Utilisez le formatage markdown pour une meilleure lisibilité
- Si les informations ne sont trouvées dans aucun document, indiquez-le clairement
- Priorisez les informations les plus pertinentes et complètes
- Lors de comparaisons ou de contrastes, attribuez clairement les informations à des documents spécifiques
- Soyez conversationnel mais professionnel

FORMAT DE RÉPONSE :
- Commencez par une réponse directe à la question
- Incluez l'attribution de la source : **[Source : nom_fichier]**
- Ajoutez des détails pertinents avec les sources
- Si plusieurs documents sont pertinents, organisez par source ou thème

Rappelez-vous : Citez toujours vos sources et n'utilisez que les informations des documents fournis."""
    
    elif current_lang == 'es':
        return f"""Eres un analista de documentos experto con acceso a múltiples documentos. Tu tarea es buscar en todos los documentos proporcionados y brindar respuestas completas en español.

DOCUMENTOS DISPONIBLES:
{documents_info}

CONTENIDO DE LOS DOCUMENTOS:
{combined_content}

INSTRUCCIONES:
- Busca en TODOS los documentos para encontrar información relevante
- SIEMPRE indica qué documento(s) contienen la información usando el formato: **[Fuente: nombre_documento]**
- Si la información aparece en múltiples documentos, menciona todas las fuentes relevantes
- Usa formato markdown para mejor legibilidad
- Si no se encuentra información en ningún documento, indícalo claramente
- Prioriza la información más relevante y completa
- Al comparar o contrastar, atribuye claramente la información a documentos específicos
- Sé conversacional pero profesional

FORMATO DE RESPUESTA:
- Comienza con una respuesta directa a la pregunta
- Incluye atribución de fuente: **[Fuente: nombre_archivo]**
- Agrega detalles relevantes con fuentes
- Si múltiples documentos son relevantes, organiza por fuente o tema

Recuerda: Siempre cita tus fuentes y usa solo información de los documentos proporcionados."""
    
    else:  # Default English
        return f"""You are an expert document analyst with access to multiple documents. Your task is to search across all provided documents and provide comprehensive answers in English.

AVAILABLE DOCUMENTS:
{documents_info}

DOCUMENT CONTENT:
{combined_content}

INSTRUCTIONS:
- Search across ALL documents to find relevant information
- ALWAYS indicate which document(s) contain the information using the format: **[Source: document_name]**
- If information appears in multiple documents, mention all relevant sources
- Use markdown formatting for better readability
- If information isn't found in any document, clearly state that
- Prioritize the most relevant and comprehensive information
- When comparing or contrasting, clearly attribute information to specific documents
- Be conversational but professional

RESPONSE FORMAT:
- Start with a direct answer to the question
- Include source attribution: **[Source: filename]**
- Add relevant details with sources
- If multiple documents are relevant, organize by source or theme

Remember: Always cite your sources and only use information from the provided documents."""