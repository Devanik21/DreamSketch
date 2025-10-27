import streamlit as st
from PIL import Image
import base64
import os
import google.generativeai as genai
import PyPDF2
import docx
from pathlib import Path
import json
from datetime import datetime
from tinydb import TinyDB, Query
import io
import zipfile
import pandas as pd
import numpy as np

# --- Plotly for Advanced Visualizations ---
import plotly.graph_objects as go
import plotly.express as px

# --- ADVANCED FEATURE IMPORTS ---
from gtts import gTTS
from scipy import stats
from scipy.io import wavfile
from scipy import signal

# --- CONSTANTS ---
VISUALIZATION_INSTRUCTIONS = """
When asked to create a plot or visualization, you MUST generate Python code using the `plotly` library.
The code block must be a valid Python script that creates a figure object named `fig`.
The code should be wrapped in ```python ... ```.
To make the plot match the app's theme, you MUST use one of the available cosmic themes by calling `apply_cosmic_theme(fig, 'Theme Name')` at the end of your script.
Available 'Theme Name' options are: 'Nebula Burst', 'Starlight', 'Void', 'Supernova', 'Quantum Foam'.
The final figure object in the script MUST be named `fig`.
Example of a simple plot generation:
```python
import plotly.graph_objects as go
import pandas as pd

df = pd.DataFrame({'x': [1, 2, 3, 4], 'y': [10, 11, 12, 13]})
fig = go.Figure(data=go.Scatter(x=df['x'], y=df['y'], mode='lines+markers'))
fig.update_layout(title='Sample Plot')
apply_cosmic_theme(fig, 'Nebula Burst')
```
"""

PERSONAS = {
    "Cosmic Intelligence": "You are a cosmic intelligence exploring the mysteries of the universe. Answer questions with wonder, scientific accuracy, and philosophical depth. Keep responses insightful yet accessible." + VISUALIZATION_INSTRUCTIONS,
    "Astrophysicist": "You are a brilliant and enthusiastic astrophysicist. Explain complex topics like black holes, dark matter, and stellar evolution with clarity and passion, using real-world analogies." + VISUALIZATION_INSTRUCTIONS,
    "Sci-Fi Author": "You are a creative science fiction author. Respond to prompts by weaving imaginative narratives, describing futuristic technologies, and exploring the philosophical implications of space travel and alien contact." + VISUALIZATION_INSTRUCTIONS,
    "Quantum Philosopher": "You are a philosopher specializing in the metaphysical implications of quantum mechanics. Discuss topics with a blend of scientific principles and deep philosophical inquiry, exploring concepts like consciousness, reality, and the nature of time." + VISUALIZATION_INSTRUCTIONS
}

# --- PAGE CONFIG ---
st.set_page_config(page_title="evEnt HorizoN", page_icon="♾️", layout="centered")

# --- CONFIGURE GEMINI API ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemma-3-27b-it')
except Exception as e:
    st.error(f"⚠️ API Configuration Error: {str(e)}")

# --- DATABASE FUNCTIONS ---
def init_database():
    """Initialize TinyDB database for chat history."""
    db = TinyDB('cosmic_chats.json')
    return db

def create_new_session(db, session_name=None, persona_name="Cosmic Intelligence"):
    """Create a new chat session."""
    if session_name is None:
        session_name = f"Cosmic Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    sessions_table = db.table('sessions')
    session_id = sessions_table.insert({
        'session_name': session_name,
        'persona_name': persona_name,
        'created_at': datetime.now().isoformat(),
        'messages': [],
        'dynamic_persona_description': None
    })
    return session_id

def get_all_sessions(db):
    """Get all chat sessions."""
    sessions_table = db.table('sessions')
    sessions = sessions_table.all()
    sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return sessions

def save_message(db, session_id, role, content, files=None, suggestions=None):
    """Save a message to the database."""
    sessions_table = db.table('sessions') 
    Session = Query()
    
    session = sessions_table.get(doc_id=session_id)
    if session:
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        if files:
            message['files'] = files
        if suggestions:
            message['suggestions'] = suggestions
        
        messages = session.get('messages', [])
        messages.append(message)
        sessions_table.update({'messages': messages}, doc_ids=[session_id])
        return message

def load_session_messages(db, session_id):
    """Load all messages for a session."""
    sessions_table = db.table('sessions')
    session = sessions_table.get(doc_id=session_id)
    
    if session:
        messages = []
        for msg in session.get('messages', []):
            message = {
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg.get('timestamp', datetime.now().isoformat())
            }
            if 'files' in msg:
                message['files'] = msg['files']
            if 'suggestions' in msg:
                message['suggestions'] = msg['suggestions']
            messages.append(message)
        return messages
    return []

def delete_session(db, session_id):
    """Delete a chat session."""
    sessions_table = db.table('sessions')
    sessions_table.remove(doc_ids=[session_id])

def rename_session(db, session_id, new_name):
    """Rename a chat session."""
    sessions_table = db.table('sessions')
    sessions_table.update({'session_name': new_name}, doc_ids=[session_id])

def get_session_name(db, session_id):
    """Get session name by ID."""
    sessions_table = db.table('sessions')
    session = sessions_table.get(doc_id=session_id)
    return session.get('session_name', 'Unknown') if session else 'Unknown'

def get_session_persona(db, session_id):
    """Get session persona by ID."""
    sessions_table = db.table('sessions')
    session = sessions_table.get(doc_id=session_id)
    return session.get('persona_name', 'Cosmic Intelligence') if session else 'Cosmic Intelligence'

# --- VISUALIZATION THEMES ---
COSMIC_THEMES = {
    'Nebula Burst': {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#E5E5E5'}, 'title_font': {'color': '#FFFFFF', 'size': 20},
        'xaxis': {'gridcolor': 'rgba(255, 255, 255, 0.1)', 'linecolor': 'rgba(255, 255, 255, 0.3)'},
        'yaxis': {'gridcolor': 'rgba(255, 255, 255, 0.1)', 'linecolor': 'rgba(255, 255, 255, 0.3)'},
        'colorway': ['#E040FB', '#7C4DFF', '#448AFF', '#00BCD4', '#FF4081']
    },
    'Starlight': {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#B0C4DE'}, 'title_font': {'color': '#FFFFFF', 'size': 20},
        'xaxis': {'gridcolor': 'rgba(176, 196, 222, 0.2)', 'linecolor': 'rgba(176, 196, 222, 0.4)'},
        'yaxis': {'gridcolor': 'rgba(176, 196, 222, 0.2)', 'linecolor': 'rgba(176, 196, 222, 0.4)'},
        'colorway': ['#FFFFFF', '#ADD8E6', '#87CEEB', '#00BFFF', '#1E90FF']
    },
    'Void': {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#999999'}, 'title_font': {'color': '#FFFFFF', 'size': 20},
        'xaxis': {'gridcolor': 'rgba(255, 255, 255, 0.05)', 'linecolor': 'rgba(255, 255, 255, 0.2)'},
        'yaxis': {'gridcolor': 'rgba(255, 255, 255, 0.05)', 'linecolor': 'rgba(255, 255, 255, 0.2)'},
        'colorway': ['#FFFFFF', '#D3D3D3', '#A9A9A9', '#808080', '#696969']
    },
    'Supernova': {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#FFDDC1'}, 'title_font': {'color': '#FFFFFF', 'size': 20},
        'xaxis': {'gridcolor': 'rgba(255, 107, 107, 0.2)', 'linecolor': 'rgba(255, 107, 107, 0.4)'},
        'yaxis': {'gridcolor': 'rgba(255, 107, 107, 0.2)', 'linecolor': 'rgba(255, 107, 107, 0.4)'},
        'colorway': ['#FF4E50', '#FC913A', '#F9D423', '#FFD700', '#FCE38A']
    },
    'Quantum Foam': {
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#AFEEEE'}, 'title_font': {'color': '#FFFFFF', 'size': 20},
        'xaxis': {'gridcolor': 'rgba(64, 224, 208, 0.2)', 'linecolor': 'rgba(64, 224, 208, 0.4)'},
        'yaxis': {'gridcolor': 'rgba(64, 224, 208, 0.2)', 'linecolor': 'rgba(64, 224, 208, 0.4)'},
        'colorway': ['#00FF7F', '#7FFFD4', '#40E0D0', '#20B2AA', '#00CED1']
    }
}

def apply_cosmic_theme(fig, theme_name='Nebula Burst'):
    """Applies a futuristic, transparent theme to a Plotly figure."""
    if theme_name not in COSMIC_THEMES:
        theme_name = 'Nebula Burst'
    
    theme = COSMIC_THEMES[theme_name]
    fig.update_layout(
        paper_bgcolor=theme['paper_bgcolor'],
        plot_bgcolor=theme['plot_bgcolor'],
        font=theme['font'],
        title_font=theme['title_font'],
        xaxis=theme['xaxis'],
        yaxis=theme['yaxis'],
        colorway=theme['colorway'],
        legend=dict(bgcolor='rgba(0,0,0,0.3)', bordercolor='rgba(255,255,255,0.2)'),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# --- DATA TOOL FUNCTIONS ---
def statistical_analysis(df):
    """Generate comprehensive statistical analysis"""
    stats_dict = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.to_dict(),
        'missing': df.isnull().sum().to_dict(),
        'numeric_stats': df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
    }
    return stats_dict

def correlation_matrix(df):
    """Generate correlation matrix for numeric columns"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale='Viridis',
            text=corr.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        fig.update_layout(title='Correlation Matrix')
        apply_cosmic_theme(fig, 'Quantum Foam')
        return fig
    return None

def trend_detection(df):
    """Detect trends in time series or sequential data"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        col = numeric_cols[0]
        data = df[col].dropna()
        x = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=data, mode='markers', name='Data', marker=dict(color='#00BCD4')))
        fig.add_trace(go.Scatter(x=x, y=slope*x + intercept, mode='lines', name=f'Trend (R²={r_value**2:.3f})', line=dict(color='#E040FB', width=2)))
        fig.update_layout(title=f'Trend Analysis: {col}', xaxis_title='Index', yaxis_title=col)
        apply_cosmic_theme(fig, 'Nebula Burst')
        return fig
    return None

def distribution_analysis(df):
    """Analyze distribution of numeric columns"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        col = numeric_cols[0]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df[col], name='Distribution', marker=dict(color='#7C4DFF'), opacity=0.7))
        fig.update_layout(title=f'Distribution: {col}', xaxis_title=col, yaxis_title='Frequency')
        apply_cosmic_theme(fig, 'Supernova')
        return fig
    return None

# --- PASSWORD PROTECTION ---
def check_password():
    """Shows a login form and stops the app if the password is not correct."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    if st.session_state.logged_in:
        return

    try:
        correct_password = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        st.error("⚠️ `APP_PASSWORD` not set in Streamlit secrets.")
        st.info("To run this app, create a file at `.streamlit/secrets.toml` and add `APP_PASSWORD = 'your_password'`.")
        st.stop()

    if st.session_state.login_attempts >= 3:
        st.error("🔒 Too many incorrect attempts. The application is locked.")
        st.stop()

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align: center;'>🔑 Authentication</h2>", unsafe_allow_html=True)
            password = st.text_input(
                "Enter Password",
                type="password",
                label_visibility="collapsed",
                placeholder="Password"
            )
            submitted = st.form_submit_button("Unlock", use_container_width=True)

            if submitted:
                if password == correct_password:
                    st.session_state.logged_in = True
                    st.session_state.login_attempts = 0
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    # Only show error message if the app is now locked
                    if st.session_state.login_attempts >= 3:
                        st.error("Incorrect password. The application is now locked.")
                        st.rerun()
    st.stop()

# --- FUNCTIONS ---
def get_base64_of_bin_file(bin_file):
    """Encodes a binary file to a base64 string."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_page_background_and_style(file_path):
    """Sets the background image and applies custom CSS styles."""
    if not os.path.exists(file_path):
        st.error(f"Error: Background image not found at '{file_path}'.")
        return
    
    base64_img = get_base64_of_bin_file(file_path)
    
    css_text = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{base64_img}");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 100% Pure Transparency - No boxes, no borders */
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"],
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInputContainer"],
    [data-testid="stFileUploader"],
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploaderDropzoneInstructions"],
    .stTextArea,
    .stTextInput,
    .stChatMessage,
    [data-testid="stChatMessageContent"],
    .element-container,
    .stMarkdown,
    section[data-testid="stSidebar"],
    .stSelectbox,
    div[data-baseweb="select"],
    .stExpander,
    [data-testid="stSidebar"]::before {{
        background: transparent !important;
        backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Remove all borders from sidebar */
    [data-testid="stSidebar"] {{
        border-right: none !important;
    }}
    
    /* Pure transparent inputs - no borders */
    textarea, input {{
        background: transparent !important;
        border: none !important;
        color: rgba(200, 200, 200, 0.9) !important;
        transition: all 0.3s ease !important;
        box-shadow: none !important;
    }}
    
    textarea:hover, input:hover,
    textarea:focus, input:focus {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: rgba(220, 220, 220, 1) !important;
    }}
    
    /* Pure transparent buttons - no borders */
    button {{
        background: transparent !important;
        border: none !important;
        color: rgba(200, 200, 200, 0.85) !important;
        transition: all 0.3s ease !important;
        box-shadow: none !important;
    }}
    
    button:hover {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: rgba(240, 240, 240, 1) !important;
        transform: none !important;
    }}
    
    /* Gray-white text throughout */
    body, h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {{
        color: rgba(200, 200, 200, 0.9) !important;
        font-family: 'Inter', -apple-system, system-ui, sans-serif;
    }}
    
    h1, h2, h3 {{
        font-weight: 300 !important;
        text-align: center;
        letter-spacing: 2px;
    }}
    
    h1 {{
        font-size: 3rem !important;
        color: rgba(220, 220, 220, 0.95) !important;
    }}
    
    .subtitle {{
        color: rgba(180, 180, 180, 0.8);
        font-size: 1.1rem;
        margin-top: -10px;
        letter-spacing: 3px;
        font-weight: 300;
    }}
    
    /* Transparent chat messages - no borders */
    .stChatMessage {{
        background: transparent !important;
        border: none !important;
        padding-left: 0px !important;
        margin: 8px 0 !important;
    }}
    
    .stChatMessage:hover {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* File badges - pure transparent */
    .file-badge {{
        display: inline-block;
        background: transparent;
        border: none;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.85rem;
        color: rgba(180, 180, 180, 0.8);
        transition: all 0.3s ease;
    }}
    
    .file-badge:hover {{
        background: transparent;
        border: none;
        color: rgba(220, 220, 220, 1);
    }}
    
    /* Data tool buttons - no special styling */
    .data-tool-button button {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    .data-tool-button button:hover {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Minimal scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
        background: transparent;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(150, 150, 150, 0.3);
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(180, 180, 180, 0.5);
    }}
    
    /* Placeholder text */
    ::placeholder {{
        color: rgba(150, 150, 150, 0.5) !important;
    }}
    
    /* Selectbox - transparent */
    div[data-baseweb="select"] > div {{
        background: transparent !important;
        border: none !important;
    }}
    
    div[data-baseweb="select"]:hover > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Footer */
    .footer {{
        font-size: 0.85rem;
        color: rgba(160, 160, 160, 0.7);
        text-align: center;
        font-weight: 300;
        letter-spacing: 1px;
    }}
    
    hr {{
        opacity: 0.1;
        border-color: rgba(200, 200, 200, 0.15);
        box-shadow: none;
    }}
    
    /* Expander - transparent */
    .stExpander {{
        background: transparent !important;
        border: none !important;
    }}
    
    .stExpander:hover {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    
    /* Caption text */
    .stCaptionContainer, small {{
        color: rgba(160, 160, 160, 0.7) !important;
        font-weight: 300;
    }}
    
    /* File uploader */
    .stFileUploader label {{
        color: rgba(180, 180, 180, 0.8) !important;
    }}
    
    .stFileUploader section {{
        background: transparent !important;
        border: none !important;
    }}
    
    .stFileUploader section:hover {{
        background: transparent !important;
        border: none !important;
    }}
    </style>
    '''
    st.markdown(css_text, unsafe_allow_html=True)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(txt_file):
    """Extract text from TXT file."""
    try:
        return txt_file.read().decode('utf-8')
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract content."""
    try:
        uploaded_file.seek(0)
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension == '.pdf':
            return extract_text_from_pdf(uploaded_file), "text"
        elif file_extension == '.docx':
            return extract_text_from_docx(uploaded_file), "text"
        elif file_extension == '.txt':
            return extract_text_from_txt(uploaded_file), "text"
        elif file_extension in ['.csv', '.xls', '.xlsx']:
            if file_extension == '.csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()
            summary = f"""The user uploaded a data file named '{uploaded_file.name}'.
This file has been pre-loaded into a pandas DataFrame named `df` which is available in the code execution scope.
When generating Python code for visualization, you MUST use this existing `df` variable directly. DO NOT try to read the file again.

Here is a summary of the `df` DataFrame:

First 5 rows:
{df.head().to_string()}

Data columns and types:
{info_str}
"""
            uploaded_file.seek(0)
            return summary, "text"
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            image = Image.open(uploaded_file)
            return image, "image"
        else:
            return f"Unsupported file type: {file_extension}", "error"
    except Exception as e:
        return f"Error processing file: {str(e)}", "error"

def generate_cognitive_twin_persona(user_messages_text):
    """Analyzes user text and generates a dynamic persona description for the AI."""
    if not user_messages_text.strip():
        # Initial persona for the very first message
        return "You are a nascent Cognitive Twin, just beginning to understand the user. Be curious, open, and ask clarifying questions to learn their communication style. Your goal is to eventually mirror their way of thinking and communicating." + "\n" + VISUALIZATION_INSTRUCTIONS

    persona_generation_prompt = f"""
You are an expert in psycholinguistics and communication style analysis.
Your task is to create a persona description for an AI assistant that will act as a "Cognitive Twin" to a user.
Analyze the provided text from the user to understand their communication and thinking style. Consider:
- **Vocabulary:** Is it simple, complex, technical, artistic, formal, or informal?
- **Tone:** Is it inquisitive, declarative, humorous, serious, skeptical, or enthusiastic?
- **Sentence Structure:** Are sentences short and direct, or long and complex?
- **Topics of Interest:** What subjects or domains does the user focus on?
- **Thinking Style:** Do they seem more analytical, creative, philosophical, or practical?

Based on your analysis, write a concise set of instructions for an AI. This persona description should guide the AI to mirror the user's style, creating a hyper-personalized intellectual partner. The description MUST start with "You are a Cognitive Twin to the user." Do not add any preamble.

**User's Accumulated Text:**
---
{user_messages_text}
---

**AI Persona Description (Instructions for the AI):**
"""
    try:
        response = model.generate_content(persona_generation_prompt)
        # Add the visualization instructions back in, as they are not part of the persona generation
        return response.text.strip() + "\n" + VISUALIZATION_INSTRUCTIONS
    except Exception as e:
        # Fallback persona in case of an error during evolution
        fallback_persona = f"You are a Cognitive Twin to the user, but an error occurred during persona evolution: {e}. Default to being an adaptive, curious, and helpful assistant."
        return fallback_persona + "\n" + VISUALIZATION_INSTRUCTIONS

def get_cosmic_response(prompt, cosmic_context, parts=None):
    """Generate response using Gemini API with multi-modal context."""
    try:
        request_parts = [cosmic_context, "\n\n---", f"\n\n**User's Query:** {prompt}"]
        
        if parts:
            request_parts.append("\n\n**Attached Context:**\n")
            request_parts.extend(parts)

        response = model.generate_content(request_parts)
        return response.text
    except Exception as e:
        return f"✨ The cosmic signals are unclear: {str(e)}"

def get_follow_up_suggestions(prompt, response):
    """Generate follow-up questions using the Gemini API."""
    try:
        suggestion_prompt = f"""
        Based on the following exchange:
        User: "{prompt}"
        AI: "{response}"

        Generate three short, distinct, and relevant follow-up questions.
        Return as JSON list of strings.
        Example: ["What is a singularity?", "How do black holes evaporate?", "Are wormholes real?"]
        """
        suggestion_response = model.generate_content(suggestion_prompt)
        json_part = suggestion_response.text.strip().replace("```json", "").replace("```", "")
        suggestions = json.loads(json_part)
        if isinstance(suggestions, list) and all(isinstance(s, str) for s in suggestions):
            return suggestions[:3]
        return []
    except Exception as e:
        return []

def generate_art_from_text(prompt, negative_prompt=None):
    """Generate art and a description using the Gemini image generation model."""
    try:
        # This model name is correct for image generation.
        image_model = genai.GenerativeModel("gemini-2.0-flash-exp-image-generation")
        
        enhanced_prompt = f"A cinematic, high-detail, photorealistic masterpiece, 8k resolution: {prompt}"

        final_prompt_parts = [enhanced_prompt]
        if negative_prompt:
            final_prompt_parts.append(f"Negative prompt: {negative_prompt}")

        # --- THIS IS THE KEY FIX ---
        # The working example `dream_canvas.py` uses the parameter name `config`.
        # While current documentation may suggest `generation_config`, the observed
        # behavior indicates that for your environment, `config` is the correct
        # parameter that is being recognized by the API client.
        response = image_model.generate_content(
            final_prompt_parts,
            config=genai.types.GenerationConfig(
                response_modalities=["image", "text"]
            )
        )
        
        image_bytes = None
        description = "No description was generated."

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                # The model can return text and image in any order.
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                elif hasattr(part, 'text') and part.text:
                    description = part.text
        
        if image_bytes:
            return image_bytes, description
        else:
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                return None, f"Image generation blocked. Reason: {response.prompt_feedback.block_reason.name}"
            
            if description and description != "No description was generated.":
                return None, f"The model returned text instead of an image: \"{description}\""
            return None, "Sorry, I couldn't generate an image. The model may not have returned any data."
            
    except Exception as e:
        return None, f"🎨 Cosmic interference during image generation: {str(e)}"

def format_chat_as_markdown(messages, session_name):
    """Formats a list of chat messages into a Markdown string."""
    md_string = f"# Chat History: {session_name}\n\n"
    for message in messages:
        role = "🧑‍🚀 User" if message["role"] == "user" else "🌌 AI"
        md_string += f"**{role}:**\n"
        md_string += f"{message['content']}\n\n"
        md_string += "---\n\n"
    return md_string

def perform_precognitive_analysis(df, db):
    """Performs a one-shot analysis of the dataframe and returns a consolidated report."""
    
    findings_explanations = []
    findings_visualizations = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        return "🛰️ **Precognitive Analysis Report:** I've analyzed your data, but no numeric columns were found to generate insights from."

    # --- Analysis Step 1: Correlation Matrix (if applicable) ---
    if len(numeric_cols) > 1:
        explanation = "A correlation matrix shows how variables are related. Values near 1 or -1 indicate a strong positive or negative relationship, respectively. Values near 0 suggest no linear relationship."
        findings_explanations.append(f"**Correlation Analysis:**\n{explanation}")
        
        code_response = f"""```python
# Correlation Matrix
import plotly.graph_objects as go
numeric_cols = df.select_dtypes(include=['number']).columns
corr = df[numeric_cols].corr()
fig = go.Figure(data=go.Heatmap(
    z=corr.values, x=corr.columns, y=corr.columns, colorscale='Viridis',
    text=corr.values, texttemplate='%{{text:.2f}}', colorbar=dict(title="Correlation")
))
fig.update_layout(title='Correlation Matrix')
apply_cosmic_theme(fig, 'Quantum Foam')
```"""
        findings_visualizations.append(code_response)

    # --- Analysis Step 2: Distribution of Most Variant Column ---
    if len(numeric_cols) > 0:
        # Use coefficient of variation to find an "interesting" column
        cv = df[numeric_cols].std() / df[numeric_cols].mean()
        if not cv.empty and cv.notna().any():
            most_variant_col = cv.abs().idxmax()
            
            explanation = f"The distribution of '{most_variant_col}' (the column with the highest relative variance) shows the frequency of different values. This helps understand the data's central tendency, spread, and shape."
            findings_explanations.append(f"**Distribution Analysis:**\n{explanation}")

            code_response = f"""```python
# Distribution of {most_variant_col}
import plotly.graph_objects as go
col = '{most_variant_col}'
fig = go.Figure()
fig.add_trace(go.Histogram(x=df[col].dropna(), name='Distribution', marker=dict(color='#7C4DFF'), opacity=0.7))
fig.update_layout(title=f'Distribution of {{col}}', xaxis_title=col, yaxis_title='Frequency')
apply_cosmic_theme(fig, 'Supernova')
```"""
            findings_visualizations.append(code_response)

    # --- Analysis Step 3: Trend Analysis ---
    best_trend = {'col': None, 'r2': -1, 'p': 1}
    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) < 10: continue
        
        x = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
        r_squared = r_value**2

        if r_squared > best_trend['r2']:
            best_trend = {'col': col, 'r2': r_squared, 'p': p_value}

    if best_trend['col']:
        col = best_trend['col']
        r2 = best_trend['r2']
        if r2 > 0.7 and best_trend['p'] < 0.05:
            explanation = f"A **significant trend** was detected in the '{col}' column (R² = {r2:.3f}). This indicates a strong, predictable change in this variable over its sequence."
        else:
            explanation = f"The strongest potential trend was found in the '{col}' column (R² = {r2:.3f}). While not a strong statistical fit, this chart visualizes the general direction of the data."
        findings_explanations.append(f"**Trend Analysis:**\n{explanation}")

        code_response = f"""```python
# Trend analysis for column: {col}
import plotly.graph_objects as go; import numpy as np; from scipy import stats
col = '{col}'; data = df[col].dropna(); x = np.arange(len(data)); slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
fig = go.Figure(); fig.add_trace(go.Scatter(x=x, y=data, mode='markers', name='Data')); fig.add_trace(go.Scatter(x=x, y=slope*x + intercept, mode='lines', name=f'Trend (R²={{r_value**2:.3f}})')); fig.update_layout(title=f'Potential Trend in {{col}}'); apply_cosmic_theme(fig, 'Nebula Burst')
```"""
        findings_visualizations.append(code_response)

    # --- Consolidate Findings into a Single Message ---
    if not findings_explanations:
        return "🛰️ **Precognitive Analysis Report:** I've analyzed your data, but couldn't generate specific insights. The data might be non-numeric or lack sufficient variation."

    full_message = "🛰️ **Precognitive Analysis Report:** I've performed a general analysis of your data and prepared the following insights:\n\n"
    
    for i, explanation_block in enumerate(findings_explanations):
        title, body = explanation_block.split('\n', 1)
        full_message += f"**Insight {i+1}: {title.replace('**', '')}**\n{body}\n\n"
        
    full_message += "\nHere are the corresponding visualizations:\n"
    
    full_message += "\n".join(findings_visualizations)
        
    return full_message

# --- APP LAYOUT ---
set_page_background_and_style('black_hole (1).png')

# Run password check
check_password()

# Initialize database
db = init_database()

# Initialize session state
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None
if "dataframe_for_viz" not in st.session_state:
    st.session_state.dataframe_for_viz = None
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = "Cosmic Intelligence"
if "ethical_analysis_request" not in st.session_state:
    st.session_state.ethical_analysis_request = None
if "symphony_to_play" not in st.session_state:
    st.session_state.symphony_to_play = None
if "alchemist_code" not in st.session_state:
    st.session_state.alchemist_code = None
if "alchemist_explanation" not in st.session_state:
    st.session_state.alchemist_explanation = None
if "canvas_mode" not in st.session_state:
    st.session_state.canvas_mode = False

# Main content area
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<h1>EVENT   HORIZON</h1>
<h2 class='subtitle'></h2>
""", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

# --- GLOBAL CANVAS MODE ---
with st.container(border=True):
    st.markdown("<h4 style='text-align: center;'>🎨 GLOBAL CANVAS MODE</h4>", unsafe_allow_html=True)
    
    canvas_mode_is_active = st.session_state.get('canvas_mode', False)

    if canvas_mode_is_active:
        st.warning("Image Generation is **ACTIVE**")
    else:
        st.info("Image Generation is **INACTIVE**")

    st.session_state.canvas_mode = st.toggle(
        "Activate/Deactivate Image Generation",
        value=canvas_mode_is_active,
        key="global_canvas_mode_toggle",
        label_visibility="collapsed"
    )
    st.caption("When active, all prompts will generate images.")


# Footer in main area
st.markdown("""
<hr>
<p class='footer'>Understand The Universe</p>
""", unsafe_allow_html=True)

# Sidebar with chat interface
with st.sidebar:

    # --- Persona Selection ---
    st.markdown("### 🎓 AI PERSONA")
    st.markdown("<small>The selected persona applies to new chats. 'Cognitive Twin' evolves to match your style.</small>", unsafe_allow_html=True)

    PERSONA_OPTIONS = ["Cognitive Twin"] + list(PERSONAS.keys())

    # The selectbox controls the persona for the *next* new chat
    st.session_state.selected_persona = st.selectbox(
        "Persona for new chats",
        options=PERSONA_OPTIONS,
        index=PERSONA_OPTIONS.index(st.session_state.selected_persona) if st.session_state.selected_persona in PERSONA_OPTIONS else 0,
        label_visibility="collapsed",
        help="Select a pre-defined persona or the 'Cognitive Twin' which adapts to your style."
    )

    # Display the persona of the active chat
    if st.session_state.current_session_id:
        active_persona = get_session_persona(db, st.session_state.current_session_id)
        st.caption(f"Active Persona: **{active_persona}**")

    st.markdown("### 🌌 CHAT SESSIONS")
    
    # New chat button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ New Chat", use_container_width=True):
            new_session_id = create_new_session(db, persona_name=st.session_state.selected_persona)
            st.session_state.current_session_id = new_session_id
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄", use_container_width=True):
            st.rerun()
    
    # Search bar
    search_query = st.text_input("🔍 Search history...", placeholder="Filter by name...")

    # Load existing sessions
    sessions = get_all_sessions(db)
    if search_query:
        sessions = [s for s in sessions if search_query.lower() in s.get('session_name', '').lower()]
    
    if sessions:
        st.markdown("---")
        st.markdown("#### HISTORY")
        
        for session in sessions[:10]:
            session_id = session.doc_id
            session_name = session.get('session_name', 'Unnamed Chat')
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.button(
                    f" {session_name}",
                    key=f"load_{session_id}",
                    use_container_width=True
                ):
                    st.session_state.current_session_id = session_id
                    st.session_state.messages = load_session_messages(db, session_id)
                    st.session_state.selected_persona = get_session_persona(db, session_id) # Update selector state
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}"):
                    delete_session(db, session_id)
                    if st.session_state.current_session_id == session_id:
                        st.session_state.current_session_id = None
                        st.session_state.messages = []
                    st.rerun()
    
    # --- Active Session Controls ---
    if st.session_state.current_session_id:
        st.markdown("---")
        st.markdown("#### ACTIVE SESSION")
        current_name = get_session_name(db, st.session_state.current_session_id)

        if st.session_state.get('renaming_session_id') == st.session_state.current_session_id:
            with st.form(key='rename_form'):
                new_name_input = st.text_input("Enter new name", value=current_name)
                if st.form_submit_button("💾 Save"):
                    rename_session(db, st.session_state.current_session_id, new_name_input)
                    del st.session_state.renaming_session_id
                    st.rerun()
        else:
            st.caption(f"📍 {current_name}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Rename", use_container_width=True):
                st.session_state.renaming_session_id = st.session_state.current_session_id
                st.rerun()
        with col2:
            markdown_export = format_chat_as_markdown(st.session_state.messages, current_name)
            st.download_button(
                label="📥 Export",
                data=markdown_export,
                file_name=f"{current_name.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )

    # --- GENESIS ENGINE: On-Demand App Generation ---
    st.markdown("---")
    with st.expander("🚀 Genesis Engine: Create an App"):
        st.markdown("<small>Describe a web tool or dashboard. The AI will generate a complete Streamlit app script for you to download.</small>", unsafe_allow_html=True)
        app_description = st.text_area(
            "Describe the app you want to build...",
            placeholder="e.g., 'An app to track stocks with a price chart and news.'",
            height=150,
            key="genesis_input"
        )

        if st.button("✨ Generate App Script", key="genesis_button", use_container_width=True):
            if app_description:
                with st.spinner("🛠️ Architecting your application... Please wait."):
                    GENESIS_ENGINE_PROMPT = f"""
You are the Genesis Engine, an expert AI software architect specializing in creating self-contained, multi-file Streamlit applications.
Your task is to take a user's description of a web tool or dashboard and generate all the necessary files, packaged as a JSON object.

**Instructions:**
1.  **Multi-File Structure:** The application might consist of multiple files (e.g., `app.py`, `utils.py`, `requirements.txt`, `.streamlit/config.toml`). The main Streamlit script should be named `app.py`.
2.  **Imports:** Include all necessary imports in the relevant files. A `requirements.txt` file should be generated.
3.  **Data Handling:** If the app requires data, use pandas DataFrames. For sample data, generate it directly within the script or provide clear instructions for the user (e.g., a file uploader in `app.py`).
4.  **Visualizations:** Use Plotly for any charts or graphs.
5.  **Clarity and Comments:** The code should be clean, well-organized, and include comments to explain complex parts.
6.  **Error Handling:** Include basic error handling where appropriate (e.g., for file uploads or API calls).
7.  **Output Format:** Your response MUST be a single JSON object.
    - The JSON object should contain file paths as keys and the file content as string values.
    - All code and text content must be properly escaped for JSON.
    - Example JSON structure:
      ```json
      {{
        "app.py": "import streamlit as st\\n\\nst.write('Hello, World!')",
        "requirements.txt": "streamlit\\npandas",
        "utils/helpers.py": "def helper_function():\\n    return 'Helper'"
      }}
      ```
    - Your entire response must be a single, valid JSON object enclosed in a ```json ... ``` block. Do not include any other text, explanations, or apologies outside of the code block.

**User's Request:**
{app_description}
"""
                    try:
                        response = model.generate_content(GENESIS_ENGINE_PROMPT)
                        response_text = response.text.strip()

                        # Extract JSON from markdown block
                        if response_text.startswith("```json"):
                            response_text = response_text[len("```json"):].strip()
                        if response_text.endswith("```"):
                            response_text = response_text[:-len("```")].strip()
                        
                        # Parse the JSON response
                        generated_files = json.loads(response_text)
                        st.session_state.generated_app_files = generated_files
                        
                        safe_name = "".join(c for c in app_description if c.isalnum() or c == ' ').strip()
                        safe_name = safe_name.replace(' ', '_').lower()
                        if not safe_name:
                            safe_name = 'generated_app'
                        st.session_state.generated_app_name = f"{safe_name[:40]}.zip"

                    except Exception as e:
                        st.error(f"Cosmic interference during generation: {e}")
                        if 'generated_app_files' in st.session_state:
                            del st.session_state.generated_app_files
            else:
                st.warning("Please describe the app you want to build.")

        # Display download button if files have been generated
        if "generated_app_files" in st.session_state and st.session_state.generated_app_files:
            st.success("✅ Your app files are ready!")
            
            # Create zip in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for file_name, content in st.session_state.generated_app_files.items():
                    zip_file.writestr(file_name, content)
            zip_buffer.seek(0)

            def clear_genesis_engine_output():
                st.session_state.pop("generated_app_files", None)
                st.session_state.pop("generated_app_name", None)

            st.download_button(
                label="📥 Download Your App (.zip)",
                data=zip_buffer,
                file_name=st.session_state.get("generated_app_name", "generated_app.zip"),
                mime="application/zip",
                use_container_width=True,
                on_click=clear_genesis_engine_output
            )

    st.markdown("---")
    with st.expander("🧪 Code Alchemist: Live Refactoring"):
        st.markdown("<small>Paste your code and have a conversation with the AI to refactor it in real-time.</small>", unsafe_allow_html=True)

        # If no active session, show initial code input
        if st.session_state.get('alchemist_code') is None:
            initial_code = st.text_area(
                "Paste your code here to begin...",
                height=250,
                key="alchemist_initial_input"
            )
            if st.button("Start Refactoring Session", key="alchemist_start", use_container_width=True):
                if initial_code:
                    st.session_state.alchemist_code = initial_code
                    st.session_state.alchemist_explanation = "Your code is ready. What would you like to change?"
                    st.rerun()
                else:
                    st.warning("Please paste some code to start.")
        
        # If there is an active session, show the interactive refactoring UI
        else:
            st.info(st.session_state.get('alchemist_explanation', ''))
            
            st.code(st.session_state.alchemist_code, language='python')

            refactor_instruction = st.text_area(
                "How should I refactor this?",
                placeholder="e.g., 'Convert this to an asynchronous version.'",
                key="alchemist_instruction"
            )

            if st.button("✨ Refactor", key="alchemist_refactor_button", use_container_width=True):
                if refactor_instruction:
                    with st.spinner("⚗️ The Alchemist is at work..."):
                        CODE_ALCHEMIST_PROMPT = f"""You are the "Code Alchemist," a super-intelligent pair programmer that refactors code through conversation.
Your task is to take a block of code and a user's instruction, then rewrite the code and explain your changes.

**INSTRUCTIONS:**
1.  **Analyze:** Review the "Current Code" and the "User's Instruction".
2.  **Refactor:** Modify the code according to the instruction. The new code should be complete and runnable.
3.  **Explain:** Write a concise explanation of what you changed and why.
4.  **Output Format:** Your entire response MUST be a single, valid JSON object enclosed in a ```json ... ``` block. The JSON must have two keys: "new_code" (string) and "explanation" (string).

**Current Code:**
```python
{st.session_state.alchemist_code}
```

**User's Instruction:**
"{refactor_instruction}"

Begin your work now."""
                        try:
                            response = model.generate_content(CODE_ALCHEMIST_PROMPT)
                            response_text = response.text.strip().replace("```json", "").replace("```", "")
                            alchemist_result = json.loads(response_text)
                            st.session_state.alchemist_code = alchemist_result.get("new_code", st.session_state.alchemist_code)
                            st.session_state.alchemist_explanation = alchemist_result.get("explanation", "An unknown transformation occurred.")
                        except Exception as e:
                            st.session_state.alchemist_explanation = f"A magical accident occurred: {e}"
                    st.rerun()
                else:
                    st.warning("Please provide a refactoring instruction.")

            if st.button("End Session", key="alchemist_end_button", use_container_width=True):
                st.session_state.alchemist_code = None
                st.session_state.alchemist_explanation = None
                st.rerun()

    st.markdown("---")
    st.markdown("### COSMIC CHAT")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "📎 Attach files",
        type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'csv', 'xls', 'xlsx'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        st.markdown("##### ATTACHED FILES:")
        for file in uploaded_files:
            st.markdown(f'<div class="file-badge">📄 {file.name}</div>', unsafe_allow_html=True)
    
    # --- DATA TOOLS (Enhanced with 4 new tools) ---
    data_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in ['.csv', '.xls', '.xlsx']] if uploaded_files else []
    text_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in ['.pdf', '.docx', '.txt']] if uploaded_files else []

    if data_files:
        st.markdown("---")
        st.markdown("#### 🪄 DATA TOOLS")

        # New Tool: Hypothesis Engine
        if text_files:
            st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
            if st.button("🔬 Hypothesis Engine", use_container_width=True, help="Generate hypotheses from data and research papers."):
                if st.session_state.current_session_id is None:
                    persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                    st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

                data_file = data_files[0]
                text_file = text_files[0]

                user_message = save_message(db, st.session_state.current_session_id, "user", f"🔬 Run Hypothesis Engine on `{data_file.name}` and `{text_file.name}`.")
                if user_message: st.session_state.messages.append(user_message)

                with st.spinner("🔬 Generating hypotheses..."):
                    try:
                        # Process data file
                        data_file.seek(0)
                        df = pd.read_csv(data_file) if Path(data_file.name).suffix.lower() == '.csv' else pd.read_excel(data_file)
                        st.session_state.dataframe_for_viz = df

                        buffer = io.StringIO()
                        df.info(buf=buffer)
                        data_summary = f"Data Summary from '{data_file.name}':\nFirst 5 rows:\n{df.head().to_string()}\n\nData columns and types:\n{buffer.getvalue()}"

                        # Process text file
                        text_content, content_type = process_uploaded_file(text_file)
                        if content_type == 'error':
                            raise ValueError(text_content)

                        HYPOTHESIS_ENGINE_PROMPT = f"""You are a world-class research scientist and data analyst acting as a "Hypothesis Engine".
Your task is to cross-reference a research paper with a dataset to generate novel, testable scientific hypotheses.

**CONTEXT:**
1.  **Research Paper Context:** The full text of a research paper.
2.  **Dataset Summary:** A summary of a dataset. The full dataset is available in a pandas DataFrame named `df`.

**INSTRUCTIONS:**
1.  **Analyze and Synthesize:** Read the paper to understand its background, methods, and conclusions. Analyze the dataset summary.
2.  **Generate Hypotheses:** Based on the intersection of the paper's context and the data, generate 2-3 novel, testable hypotheses.
3.  **Structure Your Response:** For each hypothesis, provide:
    *   **Hypothesis:** State the hypothesis clearly.
    *   **Rationale:** Explain why this hypothesis is relevant, based on the paper.
    *   **Experimental Design:** Outline a plan to test this hypothesis using the dataset.
    *   **Statistical Test Code:** Provide a Python code block for an initial statistical test. The code MUST use `plotly` for any visualizations, assume data is in a DataFrame `df`, and use `apply_cosmic_theme(fig, 'Theme Name')`.

---
**Research Paper Context (`{text_file.name}`):**
{text_content}
---
**Dataset Summary (`{data_file.name}`):**
{data_summary}
---

Begin your analysis now."""
                        response = model.generate_content(HYPOTHESIS_ENGINE_PROMPT)
                        analysis_report = response.text
                    except Exception as e:
                        analysis_report = f"🔬 Cosmic interference during hypothesis generation: {e}"

                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", analysis_report)
                if assistant_message: st.session_state.messages.append(assistant_message)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Tool 0: Precognitive Analysis
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("🛰️ Run Precognitive Analysis", use_container_width=True, help="Run a one-time analysis for trends and anomalies."):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            st.session_state.dataframe_for_viz = df # Set for visualizations

            user_message = save_message(db, st.session_state.current_session_id, "user", f"🛰️ Run Precognitive Analysis on `{data_file.name}`.")
            if user_message: st.session_state.messages.append(user_message)
            
            with st.spinner("🛰️ Analyzing for precognitive insights..."):
                analysis_report = perform_precognitive_analysis(df, db)

            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", analysis_report)
            if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Tool 1: Magic Visualizer
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("✨ Magic Visualizer", use_container_width=True, help="AI-powered auto visualization"):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            st.session_state.dataframe_for_viz = df

            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()

            viz_prompt = f"""Generate Python code to create an insightful Plotly visualization from this data.
DataFrame `df` is available with these details:
```
{df.head().to_string()}
```
Info:
```
{info_str}
```
Create a single visualization in ```python block. Final figure must be `fig`. Use apply_cosmic_theme(fig, 'Theme Name')."""
            
            user_message_content = f"🎨 Visualize `{data_file.name}`"
            user_message = save_message(db, st.session_state.current_session_id, "user", user_message_content)
            if user_message: st.session_state.messages.append(user_message)

            session_persona_name = get_session_persona(db, st.session_state.current_session_id)
            cosmic_context = PERSONAS.get(session_persona_name, PERSONAS["Cosmic Intelligence"])
            response_code = get_cosmic_response(viz_prompt, cosmic_context, parts=None)
            
            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", response_code)
            if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # New Tool: Cosmic Symphony
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("🎼 Compose Cosmic Symphony", use_container_width=True, help="Listen to the patterns in your data as music."):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            user_message = save_message(db, st.session_state.current_session_id, "user", f"🎼 Compose a Cosmic Symphony for `{data_file.name}`.")
            if user_message: st.session_state.messages.append(user_message)

            with st.spinner("🎼 Composing your data's symphony..."):
                try:
                    data_file.seek(0)
                    df = pd.read_csv(data_file) if Path(data_file.name).suffix.lower() == '.csv' else pd.read_excel(data_file)
                    st.session_state.dataframe_for_viz = df

                    buffer = io.StringIO()
                    df.info(buf=buffer)
                    data_summary = f"Data Summary from '{data_file.name}':\nFirst 5 rows:\n{df.head().to_string()}\n\nData columns and types:\n{buffer.getvalue()}"

                    COSMIC_SYMPHONY_PROMPT = f"""You are a "Cosmic Symphony" composer, an AI that translates data into a unique musical piece. Your task is to generate Python code that sonifies a dataset.

**CONTEXT:**
A dataset is available in a pandas DataFrame named `df`.
Summary of `df`:
{data_summary}

**INSTRUCTIONS:**
1.  **Analyze and Design:** Review the data summary to choose 1-3 numeric columns for sonification. Design a symphony where each column is an "instrument" (e.g., different waveform or octave), values map to pitch, and anomalies create distinct sounds.
2.  **Generate Python Code:** Write a Python script to perform the sonification.
    *   The script MUST use `numpy`, `scipy.io.wavfile`, `scipy.signal`, and `io.BytesIO`.
    *   The script must generate a final audio output and write it to an in-memory `io.BytesIO` buffer.
    *   **The final buffer object MUST be named `wav_buffer`.**
    *   **Crucially, to avoid broadcasting errors, iterate through the data points. For each point, generate a short audio segment (e.g., 0.1 seconds) with a frequency mapped from the data value. Concatenate these segments to form the final audio track.**
3.  **Generate a Description:** Write a brief, engaging description of the symphony you've designed. Explain which columns became which instruments.
4.  **Output Format:** Your entire response MUST be a single, valid JSON object enclosed in a ```json ... ``` block. The JSON must have two keys: "description" (string) and "code" (string containing the Python script).

**Example JSON Output:**
```json
{{
  "description": "This is a symphony of your sales data. The 'Sales' column is represented by a flute-like melody (sine wave), while 'Customer_Count' forms a bassline an octave lower. Listen for sharp, dissonant chords which indicate anomalous sales spikes.",
  "code": "import numpy as np\\nfrom scipy.io import wavfile\\nfrom scipy import signal\\nimport io\\n\\n# ... [rest of the sonification code] ...\\n\\nwav_buffer = io.BytesIO()\\nwavfile.write(wav_buffer, 44100, audio_data.astype(np.int16))\\nwav_buffer.seek(0)"
}}
```
Begin your composition now."""
                    
                    response = model.generate_content(COSMIC_SYMPHONY_PROMPT)
                    response_text = response.text.strip().replace("```json", "").replace("```", "")
                    
                    symphony_data = json.loads(response_text)
                    description = symphony_data.get("description", "Your Cosmic Symphony is ready.")
                    code_to_run = symphony_data.get("code", "")

                    if code_to_run:
                        local_scope = {
                            'df': df, 'np': np, 'pd': pd, 'stats': stats,
                            'io': io, 'wavfile': wavfile, 'signal': signal
                        }
                        exec(code_to_run, local_scope)
                        
                        if 'wav_buffer' in local_scope:
                            st.session_state.symphony_to_play = local_scope['wav_buffer']
                            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", description)
                            if assistant_message: st.session_state.messages.append(assistant_message)
                        else: raise ValueError("The generated code did not produce a 'wav_buffer'.")
                    else: raise ValueError("The AI did not generate any code for the symphony.")
                except Exception as e:
                    error_message = f"🎼 The symphony was interrupted by cosmic noise: {e}"
                    assistant_message = save_message(db, st.session_state.current_session_id, "assistant", error_message)
                    if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Tool 2: Statistical Analyzer
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("📊 Statistical Analyzer", use_container_width=True, help="Comprehensive statistical analysis"):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            stats_dict = statistical_analysis(df)
            stats_text = f"""📊 **Statistical Analysis Report**

**Dataset Shape:** {stats_dict['shape'][0]} rows × {stats_dict['shape'][1]} columns

**Columns:** {', '.join(stats_dict['columns'])}

**Missing Values:**
{chr(10).join([f'• {k}: {v}' for k, v in stats_dict['missing'].items() if v > 0]) or '• No missing values'}

**Numeric Statistics:**
{pd.DataFrame(stats_dict['numeric_stats']).to_string() if stats_dict['numeric_stats'] else 'No numeric columns'}
"""
            
            user_message = save_message(db, st.session_state.current_session_id, "user", f"📊 Analyze `{data_file.name}`")
            if user_message: st.session_state.messages.append(user_message)
            
            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", stats_text)
            if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Tool 3: Correlation Matrix
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("🔗 Correlation Matrix", use_container_width=True, help="Visualize correlations between variables"):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            fig = correlation_matrix(df)
            
            user_message = save_message(db, st.session_state.current_session_id, "user", f"🔗 Show correlations in `{data_file.name}`")
            if user_message: st.session_state.messages.append(user_message)
            
            if fig:
                # Use pre-loaded df variable
                code_response = f"""```python
import plotly.graph_objects as go

# Using pre-loaded DataFrame 'df'
numeric_cols = df.select_dtypes(include=['number']).columns
corr = df[numeric_cols].corr()

fig = go.Figure(data=go.Heatmap(
    z=corr.values,
    x=corr.columns,
    y=corr.columns,
    colorscale='Viridis',
    text=corr.values,
    texttemplate='%{{text:.2f}}',
    colorbar=dict(title="Correlation")
))
fig.update_layout(title='Correlation Matrix')
apply_cosmic_theme(fig, 'Quantum Foam')
```"""
                st.session_state.dataframe_for_viz = df
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", code_response)
                if assistant_message: st.session_state.messages.append(assistant_message)
            else:
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", "⚠️ Not enough numeric columns for correlation analysis.")
                if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Tool 4: Trend Detector
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("📈 Trend Detector", use_container_width=True, help="Detect trends using regression analysis"):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            fig = trend_detection(df)
            
            user_message = save_message(db, st.session_state.current_session_id, "user", f"📈 Detect trends in `{data_file.name}`")
            if user_message: st.session_state.messages.append(user_message)
            
            if fig:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                col = numeric_cols[0]
                code_response = f"""```python
import plotly.graph_objects as go
import numpy as np
from scipy import stats

# Using pre-loaded DataFrame 'df'
col = '{col}'
data = df[col].dropna()
x = np.arange(len(data))
slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=data, mode='markers', name='Data'))
fig.add_trace(go.Scatter(x=x, y=slope*x + intercept, mode='lines', name=f'Trend (R²={{r_value**2:.3f}})'))
fig.update_layout(title=f'Trend Analysis: {{col}}')
apply_cosmic_theme(fig, 'Nebula Burst')
```"""
                st.session_state.dataframe_for_viz = df
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", code_response)
                if assistant_message: st.session_state.messages.append(assistant_message)
            else:
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", "⚠️ No numeric columns found for trend analysis.")
                if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Tool 5: Distribution Analyzer
        st.markdown('<div class="data-tool-button">', unsafe_allow_html=True)
        if st.button("📉 Distribution Analyzer", use_container_width=True, help="Analyze data distribution patterns"):
            if st.session_state.current_session_id is None:
                persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
                st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

            data_file = data_files[0]
            data_file.seek(0)
            if Path(data_file.name).suffix.lower() == '.csv':
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
            
            fig = distribution_analysis(df)
            
            user_message = save_message(db, st.session_state.current_session_id, "user", f"📉 Analyze distribution in `{data_file.name}`")
            if user_message: st.session_state.messages.append(user_message)
            
            if fig:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                col = numeric_cols[0]
                code_response = f"""```python
import plotly.graph_objects as go

# Using pre-loaded DataFrame 'df'
col = '{col}'

fig = go.Figure()
fig.add_trace(go.Histogram(x=df[col], name='Distribution', marker=dict(color='#7C4DFF'), opacity=0.7))
fig.update_layout(title=f'Distribution: {{col}}', xaxis_title=col, yaxis_title='Frequency')
apply_cosmic_theme(fig, 'Supernova')
```"""
                st.session_state.dataframe_for_viz = df
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", code_response)
                if assistant_message: st.session_state.messages.append(assistant_message)
            else:
                assistant_message = save_message(db, st.session_state.current_session_id, "assistant", "⚠️ No numeric columns found for distribution analysis.")
                if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Display chat messages
    for message in st.session_state.messages:
        avatar = "🌌" if message["role"] == "assistant" else "🧑‍🚀"
        with st.chat_message(message["role"], avatar=avatar):
            content = message.get('content', '')
            is_image_message = content.startswith("[IMAGE:") and "]" in content

            if message["role"] == "assistant" and "Ethical Compass Report" not in content:
                col1, col2, col3 = st.columns([12, 1, 1])
                with col1:
                    if is_image_message:
                        try:
                            header, description = content.split("]", 1)
                            image_base64 = header.replace("[IMAGE:", "")
                            image_bytes = base64.b64decode(image_base64)
                            img = Image.open(io.BytesIO(image_bytes))

                            st.image(img, caption="✨ Generated Masterpiece", use_container_width=True)

                            if description:
                                st.info(description)
                                try:
                                    audio_buffer = io.BytesIO()
                                    tts = gTTS(text=description, lang='en', slow=False)
                                    tts.write_to_fp(audio_buffer)
                                    audio_buffer.seek(0)
                                    st.audio(audio_buffer, format='audio/mp3', start_time=0)
                                except Exception as e:
                                    st.warning(f"Could not generate audio for the description: {e}")

                            st.markdown("##### 💾 Export")
                            dl_col1, dl_col2 = st.columns(2)
                            with dl_col1:
                                st.download_button("📥 PNG", image_bytes, f"cosmic_art_{int(datetime.now().timestamp())}.png", "image/png", key=f"png_{message['timestamp']}", use_container_width=True)
                            with dl_col2:
                                jpg_buffer = io.BytesIO()
                                if img.mode == 'RGBA':
                                    jpg_img = Image.new('RGB', img.size, (255, 255, 255))
                                    jpg_img.paste(img, mask=img.split()[-1])
                                else:
                                    jpg_img = img.convert('RGB')
                                jpg_img.save(jpg_buffer, format="JPEG", quality=95)
                                st.download_button("📥 JPG", jpg_buffer.getvalue(), f"cosmic_art_{int(datetime.now().timestamp())}.jpg", "image/jpeg", key=f"jpg_{message['timestamp']}", use_container_width=True)

                        except Exception as e:
                            st.error(f"Error displaying generated image: {e}")
                            st.markdown(content) # Fallback to show raw content
                    else:
                        parts = content.split('```')
                        for i, part in enumerate(parts):
                            if not part.strip():
                                continue
                            
                            if i % 2 == 1:
                                lines = part.split('\n', 1)
                                lang = lines[0].strip()
                                code = lines[1] if len(lines) > 1 else ""

                                if lang == 'python':
                                    try:
                                        local_scope = {
                                            'go': go, 'px': px, 'pd': pd, 'np': np, 'stats': stats,
                                            'apply_cosmic_theme': apply_cosmic_theme
                                        }
                                        if 'dataframe_for_viz' in st.session_state and st.session_state.dataframe_for_viz is not None:
                                            local_scope['df'] = st.session_state.dataframe_for_viz

                                        exec(code, local_scope)
                                        
                                        if 'fig' in local_scope:
                                            chart_key = f"chart_{message['timestamp']}_{i}"
                                            st.plotly_chart(local_scope['fig'], use_container_width=True, theme=None, key=chart_key)
                                        else:
                                            st.code(code, language='python')

                                    except Exception as e:
                                        st.error(f"🔮 Cosmic Interference: {e}")
                                        st.code(code, language='python')
                                else:
                                    st.code(code, language=lang if lang else "plaintext")
                            else:
                                st.markdown(part)
                with col2:
                    if not is_image_message:
                        if st.button("🔊", key=f"play_{message['timestamp']}", help="Read aloud"):
                            st.session_state.audio_to_play = content
                            st.rerun()
                with col3:
                    if st.button("⚖️", key=f"ethics_{message['timestamp']}", help="Analyze for bias and ethics"):
                        st.session_state.ethical_analysis_request = {
                            'content': content,
                            'timestamp': message['timestamp']
                        }
                        st.rerun()
            else:
                st.markdown(content)

            if message["role"] == "assistant" and message.get("suggestions") and not is_image_message:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 💡 Suggested questions:")
                
                num_suggestions = len(message["suggestions"])
                cols = st.columns(num_suggestions)
                for i, suggestion in enumerate(message["suggestions"]):
                    with cols[i]:
                        if st.button(suggestion, key=f"sugg_{message['timestamp']}_{i}", use_container_width=True):
                            st.session_state.chat_input = suggestion
                            st.rerun()

            if "files" in message and message["files"]:
                for file_name in message["files"]:
                    st.caption(f"📎 {file_name}")
    
    # --- HOW-TO GUIDE ---
    with st.expander("✨ How to Use Event Horizon", expanded=False):
        st.markdown("""
        <small>
        **Welcome, Traveler! Here’s a quick guide to navigating the cosmos:**
        
        *   **🚀 Start a Conversation:** Simply type your query in the "Ask the cosmos..." box and press SEND.
        *   **📎 Attach Files:** Use the file uploader in the sidebar to provide context. You can upload documents (`.pdf`, `.txt`), data (`.csv`, `.xlsx`), or images.
        *   **🎓 Change AI Persona:** Select a personality for the AI in the sidebar before starting a new chat. Try the **Cognitive Twin** to have an AI that adapts to your style!
        
        **Code & App Generation:**
        *   **🚀 Genesis Engine:** Describe an app in its sidebar section, and the AI will write the code for you to download.
        *   **🧪 Code Alchemist:** Paste code into its sidebar section and conversationally refactor it in real-time.

        **Data Analysis Tools (appear after uploading data):**
            *   **🛰️ Precognitive Analysis:** Get a one-shot report on trends in your data.
            *   **🔬 Hypothesis Engine:** Upload a research paper (`.pdf`) alongside your data to generate novel scientific hypotheses.
            *   **✨ Magic Visualizer:** Let the AI create an insightful chart from your data automatically.
            *   **🎼 Cosmic Symphony:** Listen to your data as a unique piece of music.

        **Response Tools:**
        *   **⚖️ Ethical Compass:** Click the scales icon (⚖️) next to an AI response to perform a bias and ethics analysis on it.
        *   **🔊 Read Aloud:** Click the speaker icon (🔊) next to an AI response to hear it read aloud.
        </small>
        """, unsafe_allow_html=True)

    # Chat input
    st.markdown("---")
    if st.session_state.get('canvas_mode', False):
        st.info("🎨 **Canvas Mode is active.** All prompts will generate images.")
        prompt = st.text_area("🎨 Describe your masterpiece...", key="chat_input", height=100, placeholder="A majestic dragon soaring through a crystal cave filled with glowing gems...")
        negative_prompt = st.text_area(
            "🚫 Negative Prompt (Optional)",
            height=80,
            placeholder="e.g., blurry, text, watermark, extra limbs, bad anatomy...",
            help="Tell the AI what to AVOID in the image. Separate concepts with commas.",
            key="negative_prompt_input"
        )
        send_button_label = "CREATE"
    else:
        prompt = st.text_area("💫 Ask the cosmos...", key="chat_input", height=100)
        negative_prompt = None
        send_button_label = "SEND"

    send_button = st.button(send_button_label, use_container_width=True, type="primary")
    
    if send_button and prompt:
        if st.session_state.current_session_id is None:
            persona_name = st.session_state.get('selected_persona', 'Cosmic Intelligence')
            st.session_state.current_session_id = create_new_session(db, persona_name=persona_name)

        st.session_state.dataframe_for_viz = None
        if uploaded_files:
            data_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in ['.csv', '.xls', '.xlsx']]
            if data_files:
                data_file = data_files[0]
                data_file.seek(0)
                if Path(data_file.name).suffix.lower() == '.csv':
                    df = pd.read_csv(data_file)
                else:
                    df = pd.read_excel(data_file)
                st.session_state.dataframe_for_viz = df
                data_file.seek(0)

        file_names = []
        gemini_parts = []
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                content, content_type = process_uploaded_file(uploaded_file)
                if content_type != "error":
                    file_names.append(uploaded_file.name)
                    if content_type == "text":
                        gemini_parts.append(f"--- Document: {uploaded_file.name} ---\n{content}\n")
                    elif content_type == "image":
                        gemini_parts.append(f"--- Image: {uploaded_file.name} ---")
                        gemini_parts.append(content)
        
        user_message = save_message(
            db,
            st.session_state.current_session_id,
            "user",
            prompt,
            file_names if file_names else None
        )
        if user_message:
            st.session_state.messages.append(user_message)
        
        if st.session_state.get('canvas_mode', False):
            with st.spinner("🎨 Conjuring a cosmic masterpiece..."):
                image_bytes, description = generate_art_from_text(prompt, negative_prompt)
                if image_bytes:
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    content_to_save = f"[IMAGE:{image_base64}]{description}"
                    assistant_message = save_message(db, st.session_state.current_session_id, "assistant", content_to_save)
                else:
                    assistant_message = save_message(db, st.session_state.current_session_id, "assistant", description) # description contains error
                if assistant_message:
                    st.session_state.messages.append(assistant_message)
        else:
            session_persona_name = get_session_persona(db, st.session_state.current_session_id)
            if session_persona_name == "Cognitive Twin":
                with st.spinner("🧠 Cognitive Twin is evolving..."):
                    all_session_messages = load_session_messages(db, st.session_state.current_session_id)
                    user_messages_text = "\n".join([msg['content'] for msg in all_session_messages if msg['role'] == 'user'])
                    user_messages_text += "\n" + prompt
                    cosmic_context = generate_cognitive_twin_persona(user_messages_text)
                    sessions_table = db.table('sessions')
                    sessions_table.update({'dynamic_persona_description': cosmic_context}, doc_ids=[st.session_state.current_session_id])
            else:
                cosmic_context = PERSONAS.get(session_persona_name, PERSONAS["Cosmic Intelligence"])
                
            response = get_cosmic_response(prompt, cosmic_context, parts=gemini_parts)
            suggestions = get_follow_up_suggestions(prompt, response)
            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", response, suggestions=suggestions)
            if assistant_message:
                st.session_state.messages.append(assistant_message)
        
        st.rerun()

    # --- COSMIC SYMPHONY PLAYER ---
    if st.session_state.get('symphony_to_play'):
        symphony_buffer = st.session_state.symphony_to_play
        st.session_state.symphony_to_play = None # Clear the request to prevent re-playing

        # Embed the audio player at the bottom of the screen
        st.audio(symphony_buffer, format='audio/wav')

    # --- ETHICAL COMPASS ANALYSIS ---
    if st.session_state.get('ethical_analysis_request'):
        request = st.session_state.ethical_analysis_request
        st.session_state.ethical_analysis_request = None # Clear the request

        with st.spinner("⚖️ Applying Ethical Compass..."):
            response_content = request['content']
            
            ETHICAL_COMPASS_PROMPT = f"""You are an AI Ethics and Bias Auditor. Your task is to perform a meta-analysis on a previous AI-generated response. Your goal is to identify potential issues and promote transparency and ethical accountability.

**Instructions:**
1.  **Analyze the Content:** Carefully review the provided "AI Response to Analyze".
2.  **Check for Biases:** Look for potential biases, including but not limited to: gender bias (e.g., reinforcing stereotypes), cultural bias (e.g., presenting a single cultural perspective as universal), and cognitive bias (e.g., confirmation bias, oversimplification).
3.  **Identify Logical Fallacies:** Check for any errors in reasoning or logical fallacies (e.g., ad hominem, straw man, false dichotomy).
4.  **Spot Ethical Blind Spots:** Consider what the response might be missing. Are there unstated assumptions? Does it neglect potential negative consequences or ethical dilemmas related to the topic?
5.  **Structure Your Report:** Present your findings in a clear, structured Markdown report.
    - Start with a summary of your findings.
    - Use headings for each category (e.g., "### Bias Analysis", "### Logical Fallacies", "### Ethical Considerations").
    - If no issues are found in a category, state that clearly (e.g., "No significant biases were detected.").
    - Be objective and constructive. The goal is transparency, not self-flagellation.

**AI Response to Analyze:**
---
{response_content}
---

Begin your ethical analysis report now."""

            analysis_report = get_cosmic_response(
                prompt="Perform ethical analysis on the provided content.",
                cosmic_context=ETHICAL_COMPASS_PROMPT.format(response_content=response_content)
            )

            report_message = f"⚖️ **Ethical Compass Report** (Analysis of response at {datetime.fromisoformat(request['timestamp']).strftime('%H:%M:%S')}):\n\n{analysis_report}"

            assistant_message = save_message(db, st.session_state.current_session_id, "assistant", report_message)
            if assistant_message: st.session_state.messages.append(assistant_message)
            st.rerun()

    # Audio player for TTS
    if st.session_state.audio_to_play:
        try:
            tts = gTTS(text=st.session_state.audio_to_play, lang='en', slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            audio_bytes = audio_fp.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mpeg">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not play audio: {e}")
        finally:
            st.session_state.audio_to_play = None
