# setup_project.py - Project Setup and Configuration Script

import os
from pathlib import Path
import logging

def setup_project_structure():
    """Create the required project structure"""
    
    # Define project structure
    directories = [
        "data",                    # Coursework PDFs (named according to Excel file)
        "ethics_documents",        # Ethics-related documents
        "audio_responses",         # Generated audio files
        "temp_audio",             # Temporary audio files
        "translations",           # Language translation files
        "assets",                 # Logo and other assets
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create .env template if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Additional configuration
DEBUG=False
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env template file")
    
    # Create requirements.txt if it doesn't exist
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        requirements_content = """streamlit>=1.28.0
openai>=1.0.0
PyPDF2>=3.0.0
python-docx>=0.8.11
pandas>=1.5.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
pathlib
typing-extensions
"""
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        print("✅ Created requirements.txt file")
    
    # Create sample README.md
    readme_file = Path("README.md")
    if not readme_file.exists():
        readme_content = """# Roehampton University Chatbot

A guided conversation chatbot for University of Roehampton students to access coursework materials and ethics documents.

## Features

- 🔐 **Secure Authentication**: Student ID + unique code validation
- 📚 **Coursework Assistance**: Access to module-specific PDFs and Q&A
- 📋 **Ethics Guidance**: University ethics policies and guidelines
- 🌐 **Multi-language Support**: English, Arabic, French, Spanish
- 🔊 **Audio Responses**: Text-to-speech for accessibility
- 📱 **Responsive Design**: Works on desktop and mobile

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API
1. Get your OpenAI API key from https://platform.openai.com/
2. Copy your API key to the `.env` file:
```
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Prepare Your Data

#### Student Database
- Place your `student_modules_with_pdfs.xlsx` file in the project root
- Ensure it has columns: Student ID, Code, Programme, Module, PDF File

#### Coursework PDFs
- Place all coursework PDFs in the `data/` folder
- Name them exactly as specified in the Excel file's "PDF File" column
- Supported formats: PDF, DOCX

#### Ethics Documents (Optional)
- Place ethics-related documents in the `ethics_documents/` folder
- Supported formats: PDF, DOCX, TXT
- Documents will be automatically categorized by filename

### 4. Run the Application
```bash
streamlit run app.py
```

## Project Structure
```
├── app.py                          # Main application
├── localization.py                 # Multi-language support
├── ethics_handler.py               # Ethics document handler
├── student_modules_with_pdfs.xlsx  # Student database (Excel file)
├── .env                            # Environment variables
├── requirements.txt                # Python dependencies
├── data/                           # Coursework PDFs
│   ├── machine_learning.pdf
│   ├── data_visualisation.pdf
│   └── ...
├── ethics_documents/               # Ethics documents
│   ├── research_ethics.pdf
│   ├── academic_integrity.pdf
│   └── ...
├── audio_responses/                # Generated audio files
├── translations/                   # Language files
├── assets/                         # Logo and images
└── temp_audio/                     # Temporary audio files
```

## Usage Guide

### For Students

1. **Start the Application**: Visit the chatbot URL
2. **Choose Path**: Select "Ethics Document Help" or "University Coursework Help"
3. **Authentication**: Enter your Student ID and unique access code
4. **Module Selection**: Choose your enrolled module (for coursework path)
5. **Ask Questions**: Get help with your studies through AI-powered responses

### For Administrators

1. **Update Student Database**: Modify the Excel file to add/remove students
2. **Add Documents**: Place new PDFs in the appropriate folders
3. **Monitor Usage**: Check logs for system performance and issues

## Configuration Options

### Language Support
- Default languages: English, Arabic, French, Spanish
- Add new languages by updating `localization.py`
- Translation files stored in `translations/` folder

### Audio Settings
- Multiple voice options available
- Configurable in sidebar during use
- Audio files cached for performance

### Document Categories
Ethics documents are automatically categorized:
- Research Ethics Guidelines
- Student Code of Conduct  
- Academic Integrity Policies
- Data Protection & Privacy
- Complaint Procedures
- General University Policies

## Troubleshooting

### Common Issues

1. **"Student database not found"**
   - Ensure `student_modules_with_pdfs.xlsx` is in the project root
   - Check file permissions

2. **"Document not found"**
   - Verify PDF files are in the `data/` folder
   - Check filename matches exactly with Excel file

3. **"OpenAI API key missing"**
   - Add your API key to the `.env` file
   - Ensure the file is not committed to version control

4. **Authentication failures**
   - Verify Student ID and Code in the Excel file
   - Check for typos or case sensitivity

### Logs
- Application logs are displayed in the console
- Set `LOG_LEVEL=DEBUG` in `.env` for detailed logging

## Security Notes

- Student data is processed locally
- API calls to OpenAI include document content (review OpenAI's data policy)
- No persistent storage of conversations
- Session data resets on browser refresh

## Support

For technical issues:
- Check the troubleshooting section above
- Review application logs
- Contact IT support

For content issues:
- Ethics questions: ethics@roehampton.ac.uk
- Academic queries: studentservices@roehampton.ac.uk
"""

def create_sample_documents():
    """Create sample documents for testing"""
    
    # Sample ethics documents
    ethics_docs = {
        "research_ethics_guidelines.txt": """University of Roehampton Research Ethics Guidelines

1. INTRODUCTION
All research involving human participants must receive ethical approval before commencement.

2. PRINCIPLES
- Respect for persons
- Beneficence  
- Justice
- Informed consent

3. APPLICATION PROCESS
Submit your application through the Ethics Portal at least 4 weeks before starting research.

4. CONTACT
Ethics Committee: ethics@roehampton.ac.uk
""",
        
        "academic_integrity_policy.txt": """Academic Integrity Policy

DEFINITION OF PLAGIARISM
Plagiarism is the presentation of another person's work as your own without proper acknowledgment.

EXAMPLES INCLUDE:
- Copying text without quotation marks
- Paraphrasing without citation
- Submitting work previously submitted elsewhere
- Unauthorized collaboration

CONSEQUENCES
- First offense: Warning and resubmission
- Repeat offenses: Module failure or suspension

SUPPORT
Academic Skills Centre: skills@roehampton.ac.uk
""",
        
        "student_conduct_code.txt": """Student Code of Conduct

BEHAVIORAL EXPECTATIONS
Students are expected to:
- Treat others with respect and dignity
- Follow university policies and procedures
- Maintain academic honesty
- Respect university property

UNACCEPTABLE BEHAVIOR
- Harassment or discrimination
- Academic misconduct
- Substance abuse on campus
- Damage to property

REPORTING CONCERNS
Student Services: studentservices@roehampton.ac.uk
Security (urgent): ext. 3333
"""
    }
    
    # Create ethics documents
    ethics_folder = Path("ethics_documents")
    for filename, content in ethics_docs.items():
        file_path = ethics_folder / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created sample ethics document: {filename}")
    
    # Sample coursework document
    data_folder = Path("data")
    sample_coursework = data_folder / "sample_module.txt"
    if not sample_coursework.exists():
        content = """Sample Module Content

LEARNING OBJECTIVES
By the end of this module, students will be able to:
1. Understand key concepts and theories
2. Apply knowledge to practical scenarios
3. Analyze complex problems critically
4. Communicate findings effectively

ASSESSMENT METHODS
- Coursework 1: Research Report (40%)
- Coursework 2: Practical Project (40%) 
- Final Exam: Written Assessment (20%)

READING LIST
Essential Reading:
- Smith, J. (2023). Introduction to the Subject
- Brown, A. (2022). Advanced Topics

Additional Resources:
- University Library Database
- Online Learning Platform
- Study Groups

CONTACT INFORMATION
Module Leader: Dr. Example (example@roehampton.ac.uk)
Teaching Assistant: Ms. Helper (helper@roehampton.ac.uk)
"""
        with open(sample_coursework, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Created sample coursework document")

def create_sample_excel():
    """Create a sample Excel file with student data"""
    try:
        import pandas as pd
        
        # Sample student data
        sample_data = [
            ["A00034131", 3939, "MSc Data Science", "Machine Learning", "machine_learning.pdf"],
            ["A00034131", 3939, "MSc Data Science", "Data Visualisation", "data_visualisation.pdf"],
            ["A00034131", 3939, "MSc Data Science", "Statistics", "statistics.pdf"],
            ["A00034224", 8595, "MSc AI", "Deep Learning", "deep_learning.pdf"],
            ["A00034224", 8595, "MSc AI", "Neural Networks", "neural_networks.pdf"],
            ["A00034516", 6461, "MSc Business Analytics", "Data Mining", "data_mining.pdf"],
            ["A00034516", 6461, "MSc Business Analytics", "Business Intelligence", "business_intelligence.pdf"],
        ]
        
        # Create DataFrame
        df = pd.DataFrame(sample_data, columns=[
            "Student ID", "Code", "Programme", "Module", "PDF File"
        ])
        
        # Save to Excel file
        excel_file = Path("student_modules_with_pdfs.xlsx")
        if not excel_file.exists():
            df.to_excel(excel_file, index=False)
            print("✅ Created sample Excel file with student data")
            print("📝 Sample students created:")
            for _, row in df.drop_duplicates(subset=['Student ID']).iterrows():
                print(f"   - Student ID: {row['Student ID']}, Code: {row['Code']}")
    
    except ImportError:
        print("⚠️ pandas not installed. Please install it to create sample Excel file:")
        print("   pip install pandas openpyxl")

def main():
    """Main setup function"""
    print("🎓 Setting up Roehampton University Chatbot...")
    print("=" * 50)
    
    # Create project structure
    setup_project_structure()
    print()
    
    # Create sample documents
    print("📄 Creating sample documents...")
    create_sample_documents()
    print()
    
    # Create sample Excel file
    print("📊 Creating sample student database...")
    create_sample_excel()
    print()
    
    print("✅ Project setup complete!")
    print()
    print("📋 Next Steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. Replace sample Excel file with your actual student data")
    print("3. Add your coursework PDFs to the data/ folder")
    print("4. Add ethics documents to the ethics_documents/ folder")
    print("5. Install dependencies: pip install -r requirements.txt")
    print("6. Run the application: streamlit run app.py")
    print()
    print("🔗 For detailed instructions, see README.md")

if __name__ == "__main__":
    main()