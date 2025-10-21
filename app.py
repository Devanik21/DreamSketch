import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageEnhance
from io import BytesIO
import base64
import json
from gtts import gTTS
import time
import random
import uuid
import numpy as np
from sklearn.cluster import KMeans
from streamlit_drawable_canvas import st_canvas
# --- START: DATABASE PERSISTENCE SETUP ---
import os
import base64
from tinydb import TinyDB, Query


# --- START: MONKEY-PATCH V2 FOR DEPRECATED image_to_url ---
# This helper function re-creates the missing `image_to_url` functionality
# by forcing any incoming image into a non-transparent JPEG format.
import streamlit.elements.image as st_image
from PIL import Image
from io import BytesIO
import base64

# FIX V2: Force conversion to RGB and save as JPEG to eliminate all transparency issues.
def image_to_url(img, width, height, clamp, channels, output_format):
    """
    Converts a PIL Image to a base64-encoded JPEG data URL.
    """
    # Force conversion to RGB to remove any alpha (transparency) channel
    rgb_img = img.convert("RGB")
    
    # In-memory file-like object
    buffered = BytesIO()
    
    # Save the image as JPEG (a format that does not support transparency)
    rgb_img.save(buffered, format="JPEG")
    
    # Encode the bytes to a base64 string
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # Return the JPEG data URL
    return f"data:image/jpeg;base64,{img_str}"

# Overwrite the missing function with our new implementation
st_image.image_to_url = image_to_url
# --- END: MONKEY-PATCH V2 ---
# --- START: API KEY ROTATION SETUP ---
def initialize_gemini_client():
    """
    Initializes and returns a Gemini client by trying a list of API keys from secrets.
    """
    api_keys = st.secrets.get("gemini_api_keys", [])
    if not api_keys:
        st.error("API keys not found in secrets.toml. Please add them.")
        st.stop()

    if 'current_api_key_index' not in st.session_state:
        st.session_state.current_api_key_index = 0

    try:
        current_key_index = st.session_state.current_api_key_index
        api_key = api_keys[current_key_index]
        return genai.Client(api_key=api_key)
    except IndexError:
        st.error("All available API keys have reached their limit.")
        st.stop()

def rotate_api_key():
    """
    Moves to the next API key in the list.
    """
    st.session_state.current_api_key_index += 1
    st.warning("API key limit reached. Attempting to switch to the next key...")
    time.sleep(2) # Brief pause to allow UI update
# --- END: API KEY ROTATION SETUP ---

@st.cache_data
def get_base64_of_bin_file(bin_file):
    """Encodes a binary file to a base64 string."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def load_data_from_db():
    """Loads images and favorites from TinyDB into session state."""
    # Load images
    all_images = images_table.all()
    # Decode image data from base64 to bytes
    for img in all_images:
        if 'image_data_b64' in img:
            try:
                img['image_data'] = base64.b64decode(img['image_data_b64'])
            except (base64.binascii.Error, TypeError):
                # Handle potential corruption or invalid base64 string
                img['image_data'] = None # Or a placeholder image
    # Filter out any corrupted images
    st.session_state.images = [img for img in all_images if img['image_data'] is not None]

    # Load favorites
    favs_doc = favorites_table.get(doc_id=1)
    st.session_state.favorites = favs_doc['ids'] if favs_doc else []
    
    history_doc = prompt_history_table.get(doc_id=1)
    st.session_state.prompt_history = history_doc['prompts'] if history_doc else []

def save_image_to_db(image_metadata):
    """Encodes image data to Base64 and saves metadata to TinyDB."""
    db_record = image_metadata.copy()
    # Encode binary data to a base64 string for JSON compatibility
    db_record['image_data_b64'] = base64.b64encode(db_record['image_data']).decode('utf-8')
    # Remove the raw bytes data before insertion
    del db_record['image_data']
    images_table.insert(db_record)

def save_favorites_to_db():
    """Saves the current list of favorite IDs to TinyDB."""
    # First, remove any existing list of favorites.
    favorites_table.truncate()
    # Then, insert the new, updated list as the only document.
    favorites_table.insert({'ids': st.session_state.favorites})



def remove_image_from_gallery(image_id):
    """Removes a single image from the gallery and favorites, and updates the DB."""
    # Remove from the main image list in session state
    st.session_state.images = [img for img in st.session_state.images if img['id'] != image_id]

    # If the image was a favorite, remove it from there too
    if image_id in st.session_state.favorites:
        st.session_state.favorites.remove(image_id)
        save_favorites_to_db()

    # If the removed image is the one currently being viewed, update the view
    if st.session_state.current_image and st.session_state.current_image['id'] == image_id:
        st.session_state.current_image = st.session_state.images[-1] if st.session_state.images else None

    # Remove the image record from the database
    ImageQuery = Query()
    images_table.remove(ImageQuery.id == image_id)
    st.toast("🗑️ Image removed from gallery.")
    #st.rerun()

def remove_prompt_from_history(prompt_to_remove):
    """Removes a single prompt from the history and updates the DB."""
    st.session_state.prompt_history = [p for p in st.session_state.prompt_history if p != prompt_to_remove]
    save_prompt_history_to_db()
    st.toast("🗑️ Prompt removed from history.")
    


def toggle_and_save_favorite(image_id):
    """
    Universal function to add or remove an image ID from favorites
    and immediately save the entire updated list to the database.
    """
    if image_id in st.session_state.favorites:
        st.session_state.favorites.remove(image_id)
        st.toast("💔 Removed from favorites.")
    else:
        st.session_state.favorites.append(image_id)
        st.toast("⭐ Added to favorites!")
    
    save_favorites_to_db()


def save_prompt_history_to_db():
    """Saves the current prompt history list to TinyDB."""
    # First, remove any existing list of prompts.
    prompt_history_table.truncate()
    # Then, insert the new, updated list as the only document.
    prompt_history_table.insert({'prompts': st.session_state.prompt_history})

# Create a data directory if it doesn't exist
os.makedirs("data", exist_ok=True)


# Initialize the database and its tables
db = TinyDB('data/gallery_db.json')
images_table = db.table('images')
prompt_history_table = db.table('prompt_history')
favorites_table = db.table('favorites')
# --- END: DATABASE PERSISTENCE SETUP ---

# --- START: DATABASE HELPER FUNCTIONS ---



# --- END: DATABASE HELPER FUNCTIONS ---
# Page config
st.set_page_config(
    page_title="🖼️ DreamCanvas",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)



#st.sidebar.image("k5.jpg", width='stretch')



# --- START: MODIFIED SESSION STATE INITIALIZATION ---

# Initialize session state and load data only on the first run of a new session
if 'initialized' not in st.session_state:
    st.session_state.initialized = True # Mark as initialized immediately

    # Load all persistent data from the database
    load_data_from_db()

    # Set the current image to the last one in the gallery if it exists
    st.session_state.current_image = st.session_state.images[-1] if st.session_state.images else None

    # Initialize non-persistent state variables that reset with each session
    #st.session_state.prompt_history = []
    st.session_state.image_chat_history = []
    st.session_state.chat_image = None
    st.session_state.current_chat_file_id = None
    st.session_state.analyzed_prompt_text = ""
    st.session_state.current_analysis_file_id = None
    st.session_state.analysis_image = None

# --- END: MODIFIED SESSION STATE INITIALIZATION ---



    
# Otherworldly CSS with cosmic aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    :root {
        --cosmic-purple: #6366f1;
        --cosmic-blue: #0ea5e9;
        --cosmic-cyan: #06b6d4;
        --cosmic-emerald: #10b981;
        --cosmic-violet: #8b5cf6;
        --cosmic-pink: #ec4899;
        --deep-space: #0a0a0f;
        --nebula-dark: #1a1a2e;
        --star-dust: #16213e;
        --aurora-glow: rgba(99, 102, 241, 0.15);
        --text-primary: #e2e8f0;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
    }

    .rainbow-header {
    font-weight: bold;
    /* blue → teal → yellow → orange */
    background: linear-gradient(
      90deg,
      #7fa4ff 0%,
      #4cd9c0 33%,
      #ffea5d 66%,
      #ff8a65 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
    
    .stApp {
        background: radial-gradient(ellipse at top, var(--nebula-dark) 0%, var(--deep-space) 70%);
        background-attachment: fixed;
        color: var(--text-primary);
        min-height: 100vh;
        position: relative;
    }
    
    /* Make the header transparent to show the background image */
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, rgba(6, 182, 212, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }
    
    /* Floating particles effect */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.15), transparent),
            radial-gradient(1px 1px at 40px 70px, rgba(99, 102, 241, 0.3), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(236, 72, 153, 0.2), transparent),
            radial-gradient(1px 1px at 130px 80px, rgba(6, 182, 212, 0.2), transparent),
            radial-gradient(1px 1px at 160px 30px, rgba(255, 255, 255, 0.1), transparent);
        background-repeat: repeat;
        background-size: 200px 100px;
        animation: twinkle 20s linear infinite;
        pointer-events: none;
        z-index: -1;
        opacity: 0.6;
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.8; }
    }
    
    .title-container {
        background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.1) 0%,
            rgba(236, 72, 153, 0.05) 35%,
            rgba(6, 182, 212, 0.08) 70%,
            rgba(139, 92, 246, 0.1) 100%
        );
        backdrop-filter: blur(24px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin: 2rem auto;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 24px 48px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .title-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg,
            transparent 0deg,
            rgba(99, 102, 241, 0.15) 60deg,
            transparent 120deg,
            rgba(236, 72, 153, 0.1) 180deg,
            transparent 240deg,
            rgba(6, 182, 212, 0.15) 300deg,
            transparent 360deg
        );
        animation: rotate 20s linear infinite;
        z-index: -1;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .title-text {
        font-size: clamp(2.5rem, 5vw, 4rem);
        font-weight: 800;
        background: linear-gradient(
            135deg,
            #e2e8f0 0%,
            #c084fc 25%,
            #60a5fa 50%,
            #34d399 75%,
            #fbbf24 100%
        );
        background-size: 300% 300%;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 8s ease-in-out infinite;
        margin: 0;
        text-shadow: 0 0 30px rgba(99, 102, 241, 0.5);
        position: relative;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        25% { background-position: 100% 0%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
    }
    
    .subtitle {
        font-size: 1.25rem;
        color: var(--text-secondary);
        margin-top: 1rem;
        font-weight: 400;
        opacity: 0.9;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    /* Buttons with glass morphism */
    .stButton > button {
        background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.15) 0%,
            rgba(139, 92, 246, 0.15) 100%
        );
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: var(--text-primary);
        padding: 0.875rem 2rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 8px 32px rgba(99, 102, 241, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        width: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.1) 50%,
            transparent 100%
        );
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 16px 48px rgba(99, 102, 241, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        border-color: rgba(99, 102, 241, 0.5);
        background: linear-gradient(
            135deg,
            rgba(99, 102, 241, 0.25) 0%,
            rgba(139, 92, 246, 0.25) 100%
        );
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Sidebar styling */
    .stSidebar {
        background: transparent !important;
        backdrop-filter: none !important;
        border-right: none !important;
    }
    
    .stSidebar > div {
        background: transparent;
    }
    
    /* Input fields with glass effect */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(99, 102, 241, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 
            0 0 0 3px rgba(99, 102, 241, 0.15),
            0 8px 32px rgba(0, 0, 0, 0.2) !important;
        outline: none !important;
        background: rgba(99, 102, 241, 0.08) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: rgba(99, 102, 241, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }
    
    .stCheckbox > label > div > div {
        background: rgba(99, 102, 241, 0.1) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
        border-radius: 4px !important;
    }
    
    /* Headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-primary) !important;
        font-weight: 700;
    }
    
    .stMarkdown h3 {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, var(--cosmic-purple), var(--cosmic-cyan));
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Expandable sections */
    .stExpander > div > div > div > div {
        background: rgba(99, 102, 241, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom containers */
    .download-container {
        background: linear-gradient(
            135deg,
            rgba(16, 185, 129, 0.1) 0%,
            rgba(6, 182, 212, 0.1) 100%
        );
        backdrop-filter: blur(16px);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 1.5rem;
        border-radius: 20px;
        margin-top: 1rem;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
    }
    
    .image-gallery {
        background: rgba(99, 102, 241, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.15);
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .gallery-item {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .gallery-item:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(99, 102, 241, 0.15);
    }
    
    .gallery-item.selected {
        background: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
    }
    
    /* Status boxes */
    .error-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.15));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 1.25rem;
        border-radius: 16px;
        color: #fecaca;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15);
    }
    
    .success-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 1.25rem;
        border-radius: 16px;
        color: #a7f3d0;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.15);
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 1.25rem;
        border-radius: 16px;
        color: #c7d2fe;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2)) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.15);
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(5, 150, 105, 0.3)) !important;
        border-color: rgba(16, 185, 129, 0.6) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 48px rgba(16, 185, 129, 0.25);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.3);
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.5);
    }
    
    /* Loading animations */
    @keyframes pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 1; }
    }
    
    .loading-pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .title-container {
            padding: 2rem 1rem;
            margin: 1rem;
        }
        
        .title-text {
            font-size: 2.5rem;
        }
        
        .subtitle {
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- SET BACKGROUND IMAGE ---
try:
    base64_img = get_base64_of_bin_file('Gemini_Generated_Image_ici1hxici1hxici1.png')
    bg_css = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{base64_img}");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    '''
    st.markdown(bg_css, unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Background image 'k14.jpg' not found. Using default background.")
# --- END SET BACKGROUND IMAGE ---




st.markdown("""
<style>
  /* ——— Static full‑line rainbow ——— */
  .pretty-title {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    /* blue → teal → yellow → orange */
    background: linear-gradient(
      90deg,
      #7fa4ff 0%,
      #4cd9c0 33%,
      #ffea5d 66%,
      #ff8a65 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .pretty-subtitle {
    font-size: 1.2rem;
    text-align: center;
    margin-top: -0.5rem;
    /* reversed stops for contrast */
    background: linear-gradient(
      90deg,
      #ff8a65 0%,
      #ffea5d 33%,
      #4cd9c0 66%,
      #7fa4ff 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
</style>

<h1 class="pretty-title">DreamCanvas - Painting Possibilities</h1>
""", unsafe_allow_html=True)


#st.image("k11.jpg", use_container_width=True)





# Load secrets with error handling
# Initialize Gemini client using the key rotation function
client = initialize_gemini_client()

# Comprehensive style categories
# Comprehensive style categories with 300+ styles
STYLE_CATEGORIES = {
    "🎨 Classical & Renaissance": [
        "Byzantine", "Romanesque", "Gothic", "Early Renaissance", "High Renaissance", "Mannerism",
        "Northern Renaissance", "Venetian Renaissance", "Flemish Primitives", "Sfumato",
        "Chiaroscuro", "Tenebrism", "Fresco", "Tempera", "Panel painting", "Illuminated manuscript",
        "Quattrocento", "Cinquecento", "Leonardo da Vinci style", "Michelangelo style", "Raphael style"
    ],
    
    "🏛️ Baroque to Neoclassical": [
        "Baroque", "Rococo", "Neoclassicism", "Academic art", "Hudson River School",
        "Orientalism", "Romanticism", "Pre-Raphaelite", "Nazarene movement", "Biedermeier",
        "Empire style", "Regency", "Federal style", "Greek Revival", "Gothic Revival",
        "Caravaggio style", "Rubens style", "Rembrandt style", "Poussin style", "David style"
    ],
    
    "🌈 Impressionism & Post-Impressionism": [
        "Impressionism", "Neo-Impressionism", "Post-Impressionism", "Pointillism", "Divisionism",
        "Cloisonnism", "Synthetism", "Symbolism", "Art Nouveau", "Jugendstil", "Liberty style",
        "Secessionist", "Fauvism", "Expressionism", "Die Brücke", "Der Blaue Reiter",
        "Monet style", "Renoir style", "Van Gogh style", "Cézanne style", "Seurat style"
    ],
    
    "🔲 Modern Movements": [
        "Cubism", "Analytical Cubism", "Synthetic Cubism", "Futurism", "Constructivism",
        "Suprematism", "De Stijl", "Bauhaus", "Dadaism", "Surrealism", "Abstract Expressionism",
        "Color Field", "Geometric Abstraction", "Lyrical Abstraction", "Orphism", "Rayonism",
        "Picasso style", "Braque style", "Kandinsky style", "Mondrian style", "Klee style"
    ],
    
    "🎭 Contemporary & Postmodern": [
        "Pop Art", "Minimalism", "Conceptual Art", "Performance Art", "Installation Art",
        "Land Art", "Arte Povera", "Fluxus", "Neo-Expressionism", "Photorealism", "Hyperrealism",
        "Street Art", "Graffiti", "Stencil Art", "Lowbrow Art", "Neo-Pop", "Young British Artists",
        "Warhol style", "Lichtenstein style", "Hockney style", "Basquiat style", "Banksy style"
    ],
    
    "🌍 World Art Traditions": [
        "Chinese Ink Painting", "Japanese Ukiyo-e", "Sumi-e", "Nihonga", "Korean Minhwa",
        "Indian Miniature", "Mughal Painting", "Persian Miniature", "Islamic Geometric",
        "Calligraphy", "Aboriginal Dot Painting", "African Tribal", "Aztec", "Mayan",
        "Inuit Art", "Native American", "Polynesian", "Celtic", "Norse", "Slavic Folk Art"
    ],
    
    "📸 Photography Styles": [
        "Documentary Photography", "Portrait Photography", "Landscape Photography", "Street Photography",
        "Fashion Photography", "Fine Art Photography", "Architectural Photography", "Macro Photography",
        "Long Exposure", "HDR Photography", "Black and White", "Sepia", "Cross Processing",
        "Lomography", "Pinhole", "Daguerreotype", "Cyanotype", "Polaroid", "Film Photography",
        "Digital Photography", "Infrared Photography", "Underwater Photography", "Aerial Photography"
    ],
    
    "🎬 Cinematic & Visual Media": [
        "Film Noir", "German Expressionist Cinema", "Soviet Montage", "Italian Neorealism",
        "French New Wave", "Cinéma Vérité", "Spaghetti Western", "Blaxploitation",
        "Giallo", "Cyberpunk", "Steampunk", "Dieselpunk", "Atompunk", "Biopunk",
        "Solarpunk", "Cassette Futurism", "Y2K Aesthetic", "Vaporwave", "Synthwave",
        "Outrun", "Darkwave", "Retrowave", "Liminal Space", "Backrooms Aesthetic"
    ],
    
    "🎮 Digital & New Media": [
        "Digital Art", "Computer Graphics", "3D Rendering", "Pixel Art", "8-bit", "16-bit",
        "Voxel Art", "Low Poly", "Photobashing", "Matte Painting", "Concept Art",
        "Character Design", "Environment Design", "UI/UX Design", "Motion Graphics",
        "Glitch Art", "Databending", "ASCII Art", "Generative Art", "Algorithmic Art",
        "AI Art", "Neural Style Transfer", "Deep Dream", "Virtual Reality Art"
    ],
    
    "🌟 Fantasy & Science Fiction": [
        "High Fantasy", "Dark Fantasy", "Urban Fantasy", "Steampunk Fantasy", "Dieselpunk",
        "Space Opera", "Cyberpunk", "Biopunk", "Post-Apocalyptic", "Dystopian", "Utopian",
        "Retro-Futurism", "Cosmic Horror", "Gothic Horror", "Weird Fiction", "New Weird",
        "Solarpunk", "Climate Fiction", "Hard Sci-Fi", "Soft Sci-Fi", "Space Western",
        "Alternate History", "Time Travel", "Parallel Universe", "Multiverse"
    ],
    
    "🎨 Painting Techniques": [
        "Oil Painting", "Acrylic Painting", "Watercolor", "Gouache", "Tempera", "Encaustic",
        "Fresco", "Casein", "Egg Tempera", "Mixed Media", "Impasto", "Glazing", "Scumbling",
        "Alla Prima", "Wet-on-Wet", "Dry Brush", "Wash Technique", "Sgraffito", "Grisaille",
        "Underpainting", "Color Blocking", "Palette Knife", "Finger Painting", "Spray Paint"
    ],
    
    "✏️ Drawing & Illustration": [
        "Pencil Drawing", "Charcoal Drawing", "Ink Drawing", "Pen and Ink", "Crosshatching",
        "Stippling", "Conte Crayon", "Pastels", "Colored Pencils", "Markers", "Technical Drawing",
        "Architectural Drawing", "Scientific Illustration", "Medical Illustration", "Botanical Illustration",
        "Fashion Illustration", "Children's Book Illustration", "Comic Book Art", "Manga", "Manhwa",
        "Graphic Novel", "Editorial Illustration", "Advertising Illustration", "Logo Design"
    ],
    
    "🏺 Sculpture & 3D Arts": [
        "Classical Sculpture", "Modern Sculpture", "Abstract Sculpture", "Kinetic Sculpture",
        "Installation Art", "Land Art", "Environmental Art", "Public Art", "Monument",
        "Bas-Relief", "High Relief", "Carving", "Casting", "Modeling", "Assemblage",
        "Found Object Art", "Readymade", "Welded Sculpture", "Ceramic Sculpture", "Glass Art",
        "Ice Sculpture", "Sand Sculpture", "Digital Sculpture", "3D Printing Art"
    ],
    
    "🎪 Decorative & Applied Arts": [
        "Art Deco", "Art Nouveau", "Arts and Crafts Movement", "Bauhaus Design", "Memphis Design",
        "Mid-Century Modern", "Scandinavian Design", "Japanese Minimalism", "Industrial Design",
        "Product Design", "Interior Design", "Textile Design", "Pattern Design", "Wallpaper Design",
        "Ceramic Art", "Pottery", "Porcelain", "Glassblowing", "Stained Glass", "Mosaic",
        "Marquetry", "Intarsia", "Woodworking", "Metalworking", "Jewelry Design"
    ],
    
    "📚 Printmaking & Graphic Arts": [
        "Woodcut", "Engraving", "Etching", "Lithography", "Screen Printing", "Monotype",
        "Linocut", "Mezzotint", "Aquatint", "Drypoint", "Collagraph", "Photogravure",
        "Risograph", "Letterpress", "Typography", "Calligraphy", "Hand Lettering",
        "Poster Design", "Book Design", "Magazine Layout", "Newspaper Design", "Packaging Design",
        "Logo Design", "Corporate Identity", "Branding", "Infographic Design"
    ],
    
    "🌈 Color & Light Studies": [
        "Monochromatic", "Analogous Colors", "Complementary Colors", "Triadic Colors", "Split Complementary",
        "Warm Palette", "Cool Palette", "Earth Tones", "Pastel Colors", "Neon Colors",
        "High Contrast", "Low Contrast", "Chiaroscuro", "Tenebrism", "Sfumato",
        "Atmospheric Perspective", "Linear Perspective", "Color Temperature", "Saturation Studies",
        "Value Studies", "Light Studies", "Shadow Studies", "Reflection Studies", "Refraction"
    ],
    
    "🔮 Surreal & Visionary": [
        "Surrealism", "Magic Realism", "Visionary Art", "Psychedelic Art", "Outsider Art",
        "Art Brut", "Naive Art", "Folk Art", "Primitive Art", "Shamanic Art",
        "Sacred Geometry", "Mandala", "Fractal Art", "Optical Illusions", "Trompe-l'oeil",
        "Anamorphosis", "Impossible Objects", "Dream Imagery", "Nightmare Imagery", "Mythological",
        "Allegorical", "Symbolic", "Metaphysical", "Transcendental", "Spiritual Art"
    ],
    
    "⚡ Experimental & Avant-Garde": [
        "Abstract Expressionism", "Action Painting", "Color Field Painting", "Hard Edge",
        "Geometric Abstraction", "Lyrical Abstraction", "Minimalism", "Process Art", "Systems Art",
        "Conceptual Art", "Performance Art", "Video Art", "Sound Art", "Light Art",
        "Kinetic Art", "Op Art", "Neo-Geo", "Pictures Generation", "Institutional Critique",
        "Relational Aesthetics", "Post-Internet Art", "Net Art", "Bio Art", "Eco Art"
    ],
    
    "🎭 Cultural Fusion": [
        "Afrofuturism", "Chicano Art", "Indigenous Futurism", "Decolonial Art", "Postcolonial Art",
        "Diaspora Art", "Hybrid Cultures", "Cultural Appropriation Critique", "Identity Art",
        "Queer Art", "Feminist Art", "Intersectional Art", "Social Practice Art", "Community Art",
        "Activist Art", "Protest Art", "Political Art", "Propaganda Art", "Agitprop",
        "Counter-Culture", "Underground Comics", "Zine Aesthetic", "Punk Aesthetic", "Goth Aesthetic"
    ],
    
    "🚀 Futuristic & Speculative": [
        "Post-Human Art", "Transhumanist Art", "Xenoarchaeology", "Speculative Design", "Critical Design",
        "Bio-Art", "Genetic Art", "Nano Art", "Quantum Art", "Holographic Art",
        "Augmented Reality Art", "Virtual Reality Art", "Mixed Reality Art", "Metaverse Art",
        "Blockchain Art", "NFT Art", "Cryptocurrency Art", "Post-Digital Art", "New Materialism",
        "Object-Oriented Ontology", "Accelerationist Aesthetics", "Xenofeminism", "Cosmotechnics"
    ]
}

# Sidebar for advanced options
with st.sidebar:
    st.markdown("### 🎨 Creative Controls")
    
    # Style selection
    selected_category = st.selectbox("🎭 Style Category", list(STYLE_CATEGORIES.keys()))
    selected_style = st.selectbox("✨ Specific Style", STYLE_CATEGORIES[selected_category])
    
    # Advanced settings
    st.markdown("### ⚙️ Advanced Settings")
    
    # Image dimensions
    aspect_ratio = st.selectbox("📐 Aspect Ratio", [
        "Square (1:1)", "Portrait (3:4)", "Landscape (4:3)", 
        "Wide (16:9)", "Ultra-wide (21:9)", "Vertical (9:16)"
    ])
    
    # Quality settings
    quality_level = st.selectbox("💎 Quality", ["Standard", "High", "Ultra"])
    
    # Color palette
    color_mood = st.selectbox("🎨 Color Mood", [
        "Natural", "Vibrant", "Pastel", "Monochrome", "Warm tones", 
        "Cool tones", "Neon", "Earth tones", "Vintage", "High contrast"
    ])
    
    # Lighting
# Lighting
    lighting = st.selectbox("💡 Lighting", [
        "Natural", "Dramatic", "Soft", "Studio", "Golden hour", 
        "Blue hour", "Neon", "Candlelight", "Harsh", "Backlit"
    ])
        # ADD THIS SLIDER FOR TEMPERATURE CONTROL
    temperature = st.slider(
        "🌡️ Temperature (Creativity)",
        min_value=0.0,
        max_value=2.0,
        value=0.9,
        step=0.05,
        help="Controls the randomness of the output. Lower values are more predictable, higher values are more creative."
    )
    

    

# Mood presets - INSERT THIS SECTION HERE
    mood_preset = st.selectbox("🌙 Mood Presets", [
        "Custom", "Dreamy", "Ethereal", "Mystical", "Serene", 
        "Nostalgic", "Romantic", "Melancholic", "Whimsical", "Surreal",
        "Dark Fantasy", "Cyberpunk", "Steampunk", "Art Deco", "Minimalist",
        "Baroque", "Gothic", "Renaissance", "Abstract", "Pop Art",
        "Vintage Hollywood", "Film Noir", "Retro Futuristic", "Psychedelic", "Grunge",
        "Kawaii", "Brutalist", "Vaporwave", "Cottagecore", "Dark Academia",
        "Tropical", "Arctic", "Desert", "Forest", "Ocean",
        "Urban", "Rural", "Industrial", "Pastoral", "Metropolitan",
        "Bohemian", "Elegant", "Rustic", "Modern", "Classical",
        "Dramatic", "Peaceful", "Energetic", "Contemplative", "Mysterious",
        "Joyful", "Somber", "Intense", "Gentle", "Bold",
        "Delicate", "Powerful", "Soft", "Sharp", "Flowing",
        "Geometric", "Organic", "Structured", "Free-form", "Symmetrical",
        "Asymmetrical", "Monochromatic", "Colorful", "Muted", "Vibrant",
        "Pastel Dreams", "Neon Nights", "Earth Tones", "Jewel Tones", "Metallic",
        "Watercolor", "Oil Painting", "Digital Art", "Mixed Media", "Collage",
        "Photography", "Illustration", "Sculpture", "Architecture", "Typography",
        "Fairy Tale", "Horror", "Sci-Fi", "Western", "Adventure",
        "Romance", "Thriller", "Comedy", "Drama", "Documentary",
        "Ancient", "Medieval", "Victorian", "Art Nouveau", "Bauhaus",
        "Impressionist", "Expressionist", "Cubist", "Dadaist", "Futurist",
        "Constructivist", "Surrealist", "Abstract Expressionist", "Pop", "Minimalist Movement",
        "Japanese", "Chinese", "Indian", "African", "Native American",
        "Scandinavian", "Mediterranean", "Middle Eastern", "Latin American", "European",
        "Morning Mist", "Afternoon Sun", "Evening Glow", "Midnight Blue", "Dawn Light"
    ])
    
    # Mood preset configurations
    MOOD_PRESETS = {
        "Dreamy": {
            "styles": ["Dream Imagery", "Sfumato", "Impressionism", "Symbolism"],
            "color_mood": "Pastel",
            "lighting": "Soft",
            "enhancement": "soft focus, ethereal glow, floating elements, misty atmosphere"
        },
        "Ethereal": {
            "styles": ["Visionary Art", "Magic Realism", "Symbolism"],
            "color_mood": "Cool tones", 
            "lighting": "Blue hour",
            "enhancement": "translucent, ghostly, luminous, otherworldly atmosphere"
        },
        "Mystical": {
            "styles": ["High Fantasy", "Sacred Geometry", "Mandala"],
            "color_mood": "Warm tones",
            "lighting": "Golden hour", 
            "enhancement": "magical aura, ancient symbols, mystical energy, enchanted"
        },
        "Serene": {
            "styles": ["Japanese Minimalism", "Sumi-e", "Impressionism"],
            "color_mood": "Natural",
            "lighting": "Natural",
            "enhancement": "peaceful, calm waters, gentle breeze, tranquil setting"
        },
        "Nostalgic": {
            "styles": ["Vintage", "Sepia", "Film Photography"],
            "color_mood": "Vintage",
            "lighting": "Golden hour",
            "enhancement": "faded memories, old photographs, sepia tones, nostalgic warmth"
        },
        "Romantic": {
            "styles": ["Rococo", "Impressionism", "Art Nouveau"],
            "color_mood": "Pastel",
            "lighting": "Candlelight",
            "enhancement": "soft roses, gentle breeze, romantic sunset, tender moments"
        },
        "Surreal": {
            "styles": ["Surrealism", "Dream Imagery", "Magic Realism"],
            "color_mood": "Vibrant",
            "lighting": "Dramatic",
            "enhancement": "impossible geometry, floating objects, dream logic, surreal landscapes"
        },
        "Dark Fantasy": {
            "styles": ["Gothic Art", "Dark Fantasy", "Medieval"],
            "color_mood": "Dark tones",
            "lighting": "Dramatic shadows",
            "enhancement": "ancient castles, mystical creatures, shadowy forests, magical darkness"
        },
        "Cyberpunk": {
            "styles": ["Neon Noir", "Digital Art", "Futuristic"],
            "color_mood": "Neon",
            "lighting": "Neon lights",
            "enhancement": "holographic displays, rain-soaked streets, cybernetic implants, urban decay"
        },
        "Steampunk": {
            "styles": ["Victorian", "Industrial", "Retro-futuristic"],
            "color_mood": "Brass and copper",
            "lighting": "Gas lamp",
            "enhancement": "brass gears, steam pipes, clockwork mechanisms, airships"
        },
        "Art Deco": {
            "styles": ["Geometric", "Luxurious", "1920s"],
            "color_mood": "Gold and black",
            "lighting": "Dramatic",
            "enhancement": "geometric patterns, elegant lines, luxurious materials, metropolitan glamour"
        },
        "Minimalist": {
            "styles": ["Clean lines", "Negative space", "Simple forms"],
            "color_mood": "Monochromatic",
            "lighting": "Even",
            "enhancement": "clean composition, essential elements only, white space, geometric simplicity"
        },
        "Baroque": {
            "styles": ["Ornate", "Classical", "Dramatic"],
            "color_mood": "Rich",
            "lighting": "Chiaroscuro",
            "enhancement": "elaborate details, dramatic contrasts, ornamental flourishes, grandeur"
        },
        "Gothic": {
            "styles": ["Medieval", "Dark", "Architectural"],
            "color_mood": "Dark and moody",
            "lighting": "Cathedral light",
            "enhancement": "pointed arches, stained glass, stone gargoyles, mysterious shadows"
        },
        "Renaissance": {
            "styles": ["Classical realism", "Perspective", "Harmony"],
            "color_mood": "Warm earth tones",
            "lighting": "Natural daylight",
            "enhancement": "perfect proportions, classical subjects, architectural elements, masterful technique"
        },
        "Abstract": {
            "styles": ["Non-representational", "Color field", "Geometric abstraction"],
            "color_mood": "Bold contrasts",
            "lighting": "Varied",
            "enhancement": "pure form and color, non-figurative elements, emotional expression through abstraction"
        },
        "Pop Art": {
            "styles": ["Bold graphics", "Commercial imagery", "Bright colors"],
            "color_mood": "Primary colors",
            "lighting": "Flat",
            "enhancement": "bold outlines, comic book style, mass culture references, repetitive patterns"
        },
        "Vintage Hollywood": {
            "styles": ["Glamour photography", "Golden age", "Star portraits"],
            "color_mood": "Black and white",
            "lighting": "Studio lighting",
            "enhancement": "classic glamour, star quality, vintage fashion, old Hollywood elegance"
        },
        "Film Noir": {
            "styles": ["High contrast", "Shadow play", "Urban scenes"],
            "color_mood": "Black and white",
            "lighting": "Low key",
            "enhancement": "venetian blind shadows, rain-slicked streets, cigarette smoke, mystery"
        },
        "Retro Futuristic": {
            "styles": ["1950s sci-fi", "Atomic age", "Space age"],
            "color_mood": "Atomic colors",
            "lighting": "Neon and chrome",
            "enhancement": "flying cars, robots, atomic symbols, chrome finishes, space age design"
        },
        "Psychedelic": {
            "styles": ["Kaleidoscopic", "Fractal", "Optical illusion"],
            "color_mood": "Rainbow",
            "lighting": "Blacklight",
            "enhancement": "swirling patterns, kaleidoscope effects, mind-bending visuals, consciousness expansion"
        },
        "Grunge": {
            "styles": ["Distressed", "Raw", "Underground"],
            "color_mood": "Muted and dirty",
            "lighting": "Harsh",
            "enhancement": "texture overlays, distressed effects, urban decay, raw authenticity"
        },
        "Kawaii": {
            "styles": ["Cute", "Pastel", "Japanese pop"],
            "color_mood": "Pastel rainbow",
            "lighting": "Soft and bright",
            "enhancement": "adorable characters, pastel colors, sparkles, cute expressions, playful elements"
        },
        "Brutalist": {
            "styles": ["Concrete", "Geometric", "Monumental"],
            "color_mood": "Concrete gray",
            "lighting": "Harsh shadows",
            "enhancement": "raw concrete, massive forms, geometric repetition, monumental scale"
        },
        "Vaporwave": {
            "styles": ["80s aesthetic", "Neon grid", "Retro digital"],
            "color_mood": "Pink and cyan",
            "lighting": "Neon glow",
            "enhancement": "grid landscapes, retro computers, neon palm trees, synthwave aesthetics"
        },
        "Cottagecore": {
            "styles": ["Rural", "Handcraft", "Natural"],
            "color_mood": "Earthy pastels",
            "lighting": "Golden hour",
            "enhancement": "wildflowers, rustic cottage, handmade crafts, peaceful countryside"
        },
        "Dark Academia": {
            "styles": ["Classical", "Scholarly", "Gothic revival"],
            "color_mood": "Deep browns and greens",
            "lighting": "Library lighting",
            "enhancement": "old books, ivy-covered buildings, vintage typewriters, scholarly atmosphere"
        },
        "Tropical": {
            "styles": ["Lush", "Vibrant", "Paradise"],
            "color_mood": "Bright tropical",
            "lighting": "Sunny",
            "enhancement": "palm fronds, exotic flowers, turquoise waters, tropical paradise"
        },
        "Arctic": {
            "styles": ["Minimalist", "Stark", "Pure"],
            "color_mood": "Ice blue and white",
            "lighting": "Arctic light",
            "enhancement": "ice formations, aurora borealis, pristine snow, crystalline structures"
        },
        "Desert": {
            "styles": ["Vast", "Minimalist", "Warm"],
            "color_mood": "Sand and terracotta",
            "lighting": "Desert sun",
            "enhancement": "sand dunes, cactus silhouettes, endless horizons, desert mirages"
        },
        "Forest": {
            "styles": ["Natural", "Organic", "Mystical"],
            "color_mood": "Forest greens",
            "lighting": "Dappled sunlight",
            "enhancement": "ancient trees, moss-covered stones, woodland creatures, forest magic"
        },
        "Ocean": {
            "styles": ["Fluid", "Dynamic", "Deep"],
            "color_mood": "Ocean blues",
            "lighting": "Underwater",
            "enhancement": "coral reefs, flowing currents, marine life, oceanic depths"
        },
        "Urban": {
            "styles": ["Metropolitan", "Contemporary", "Energetic"],
            "color_mood": "City lights",
            "lighting": "Streetlight",
            "enhancement": "skyscrapers, busy streets, neon signs, urban energy"
        },
        "Rural": {
            "styles": ["Pastoral", "Simple", "Peaceful"],
            "color_mood": "Natural earth tones",
            "lighting": "Country light",
            "enhancement": "rolling hills, farm fields, country roads, rustic barns"
        },
        "Industrial": {
            "styles": ["Mechanical", "Raw", "Functional"],
            "color_mood": "Metal and rust",
            "lighting": "Factory lighting",
            "enhancement": "steel beams, machinery, pipes, industrial textures"
        },
        "Pastoral": {
            "styles": ["Idyllic", "Romantic", "Natural"],
            "color_mood": "Soft greens",
            "lighting": "Pastoral light",
            "enhancement": "sheep in meadows, babbling brooks, wildflower fields, peaceful countryside"
        },
        "Metropolitan": {
            "styles": ["Sophisticated", "Cosmopolitan", "Dynamic"],
            "color_mood": "Urban sophistication",
            "lighting": "City glow",
            "enhancement": "glass towers, cultural venues, diverse crowds, metropolitan sophistication"
        },
        "Bohemian": {
            "styles": ["Eclectic", "Artistic", "Free-spirited"],
            "color_mood": "Rich jewel tones",
            "lighting": "Warm ambient",
            "enhancement": "tapestries, vintage furniture, artistic clutter, bohemian lifestyle"
        },
        "Elegant": {
            "styles": ["Refined", "Sophisticated", "Luxurious"],
            "color_mood": "Sophisticated neutrals",
            "lighting": "Refined",
            "enhancement": "fine materials, graceful lines, understated luxury, timeless beauty"
        },
        "Rustic": {
            "styles": ["Weathered", "Natural", "Handmade"],
            "color_mood": "Weathered wood tones",
            "lighting": "Natural rustic",
            "enhancement": "reclaimed wood, stone textures, handcrafted details, natural patina"
        },
        "Modern": {
            "styles": ["Clean", "Functional", "Contemporary"],
            "color_mood": "Contemporary palette",
            "lighting": "Clean modern",
            "enhancement": "sleek lines, minimal ornamentation, functional beauty, contemporary design"
        },
        "Classical": {
            "styles": ["Timeless", "Balanced", "Harmonious"],
            "color_mood": "Classical harmony",
            "lighting": "Balanced",
            "enhancement": "perfect proportions, classical orders, timeless beauty, mathematical harmony"
        },
        "Dramatic": {
            "styles": ["High contrast", "Bold", "Theatrical"],
            "color_mood": "High contrast",
            "lighting": "Dramatic lighting",
            "enhancement": "strong shadows, bold gestures, theatrical elements, emotional intensity"
        },
        "Peaceful": {
            "styles": ["Calm", "Harmonious", "Balanced"],
            "color_mood": "Peaceful tones",
            "lighting": "Gentle",
            "enhancement": "still waters, gentle breezes, harmonious compositions, tranquil atmosphere"
        },
        "Energetic": {
            "styles": ["Dynamic", "Vibrant", "Active"],
            "color_mood": "Energetic brights",
            "lighting": "High energy",
            "enhancement": "motion blur, dynamic poses, vibrant energy, active movement"
        },
        "Contemplative": {
            "styles": ["Thoughtful", "Meditative", "Introspective"],
            "color_mood": "Contemplative hues",
            "lighting": "Soft contemplative",
            "enhancement": "quiet spaces, reflective surfaces, meditative poses, inner peace"
        },
        "Mysterious": {
            "styles": ["Enigmatic", "Shadowy", "Unknown"],
            "color_mood": "Mystery tones",
            "lighting": "Mysterious shadows",
            "enhancement": "hidden details, veiled figures, fog and mist, unknown elements"
        },
        "Joyful": {
            "styles": ["Bright", "Cheerful", "Uplifting"],
            "color_mood": "Joyful brights",
            "lighting": "Bright and cheerful",
            "enhancement": "smiling faces, bright colors, celebratory elements, positive energy"
        },
        "Somber": {
            "styles": ["Serious", "Melancholic", "Reflective"],
            "color_mood": "Muted and somber",
            "lighting": "Subdued",
            "enhancement": "quiet reflection, subdued colors, serious expressions, contemplative mood"
        },
        "Intense": {
            "styles": ["Powerful", "Concentrated", "Focused"],
            "color_mood": "Intense colors",
            "lighting": "Intense",
            "enhancement": "concentrated energy, focused attention, powerful emotions, high intensity"
        },
        "Gentle": {
            "styles": ["Soft", "Tender", "Kind"],
            "color_mood": "Gentle pastels",
            "lighting": "Gentle soft",
            "enhancement": "soft textures, tender moments, gentle expressions, kind gestures"
        },
        "Bold": {
            "styles": ["Strong", "Confident", "Assertive"],
            "color_mood": "Bold statement colors",
            "lighting": "Bold lighting",
            "enhancement": "strong statements, confident poses, assertive compositions, bold choices"
        },
        "Delicate": {
            "styles": ["Fine", "Subtle", "Refined"],
            "color_mood": "Delicate tints",
            "lighting": "Delicate",
            "enhancement": "fine details, subtle textures, delicate forms, refined elegance"
        },
        "Powerful": {
            "styles": ["Strong", "Commanding", "Dominant"],
            "color_mood": "Power colors",
            "lighting": "Powerful",
            "enhancement": "strong forms, commanding presence, dominant elements, powerful impact"
        },
        "Soft": {
            "styles": ["Gentle", "Smooth", "Flowing"],
            "color_mood": "Soft tones",
            "lighting": "Soft diffused",
            "enhancement": "smooth transitions, gentle curves, soft textures, flowing lines"
        },
        "Sharp": {
            "styles": ["Precise", "Angular", "Crisp"],
            "color_mood": "High contrast sharp",
            "lighting": "Sharp precise",
            "enhancement": "crisp edges, angular forms, precise details, sharp contrasts"
        },
        "Flowing": {
            "styles": ["Fluid", "Curved", "Organic"],
            "color_mood": "Flowing gradients",
            "lighting": "Flowing light",
            "enhancement": "curved lines, fluid motion, organic forms, graceful movement"
        },
        "Geometric": {
            "styles": ["Mathematical", "Structured", "Precise"],
            "color_mood": "Geometric primaries",
            "lighting": "Structured",
            "enhancement": "perfect geometry, mathematical precision, structured compositions, geometric patterns"
        },
        "Organic": {
            "styles": ["Natural", "Irregular", "Flowing"],
            "color_mood": "Natural organic",
            "lighting": "Natural organic",
            "enhancement": "natural forms, irregular patterns, organic textures, living systems"
        },
        "Structured": {
            "styles": ["Organized", "Systematic", "Ordered"],
            "color_mood": "Ordered palette",
            "lighting": "Systematic",
            "enhancement": "clear organization, systematic arrangement, ordered elements, structured design"
        },
        "Free-form": {
            "styles": ["Spontaneous", "Unstructured", "Expressive"],
            "color_mood": "Spontaneous colors",
            "lighting": "Free-form",
            "enhancement": "spontaneous gestures, unstructured composition, expressive freedom, creative spontaneity"
        },
        "Symmetrical": {
            "styles": ["Balanced", "Mirrored", "Harmonious"],
            "color_mood": "Balanced symmetry",
            "lighting": "Symmetrical",
            "enhancement": "perfect balance, mirrored elements, symmetrical composition, harmonious arrangement"
        },
        "Asymmetrical": {
            "styles": ["Unbalanced", "Dynamic", "Tension"],
            "color_mood": "Dynamic imbalance",
            "lighting": "Asymmetrical",
            "enhancement": "dynamic tension, unbalanced composition, visual interest, creative asymmetry"
        },
        "Monochromatic": {
            "styles": ["Single color", "Tonal variation", "Unity"],
            "color_mood": "Single color family",
            "lighting": "Monochromatic",
            "enhancement": "tonal variations, unified color scheme, subtle gradations, monochromatic harmony"
        },
        "Colorful": {
            "styles": ["Multi-hued", "Vibrant", "Diverse"],
            "color_mood": "Full spectrum",
            "lighting": "Colorful",
            "enhancement": "rainbow colors, vibrant diversity, colorful celebration, chromatic richness"
        },
        "Muted": {
            "styles": ["Subdued", "Understated", "Soft"],
            "color_mood": "Muted tones",
            "lighting": "Muted",
            "enhancement": "subdued colors, understated elegance, soft color harmony, muted sophistication"
        },
        "Vibrant": {
            "styles": ["Intense", "Saturated", "Lively"],
            "color_mood": "Highly saturated",
            "lighting": "Vibrant",
            "enhancement": "saturated colors, intense vibrancy, lively energy, color intensity"
        },
        "Pastel Dreams": {
            "styles": ["Soft pastels", "Dreamy", "Ethereal"],
            "color_mood": "Dreamy pastels",
            "lighting": "Soft dreamy",
            "enhancement": "cotton candy colors, dreamy atmosphere, soft clouds, pastel paradise"
        },
        "Neon Nights": {
            "styles": ["Electric", "Glowing", "Urban"],
            "color_mood": "Electric neon",
            "lighting": "Neon glow",
            "enhancement": "glowing signs, electric atmosphere, night city, neon reflections"
        },
        "Earth Tones": {
            "styles": ["Natural", "Grounded", "Organic"],
            "color_mood": "Earth palette",
            "lighting": "Earth tones",
            "enhancement": "natural materials, earth pigments, grounded feeling, organic harmony"
        },
        "Jewel Tones": {
            "styles": ["Rich", "Luxurious", "Deep"],
            "color_mood": "Precious gems",
            "lighting": "Jewel lighting",
            "enhancement": "emerald greens, sapphire blues, ruby reds, precious stone colors"
        },
        "Metallic": {
            "styles": ["Reflective", "Industrial", "Precious"],
            "color_mood": "Metal finishes",
            "lighting": "Metallic reflections",
            "enhancement": "chrome surfaces, gold accents, silver highlights, metallic sheens"
        },
        "Watercolor": {
            "styles": ["Fluid", "Transparent", "Organic"],
            "color_mood": "Watercolor washes",
            "lighting": "Transparent",
            "enhancement": "color bleeding, transparent washes, paper texture, fluid boundaries"
        },
        "Oil Painting": {
            "styles": ["Rich", "Textured", "Classical"],
            "color_mood": "Oil pigments",
            "lighting": "Classical painting",
            "enhancement": "thick impasto, rich colors, canvas texture, painterly brushstrokes"
        },
        "Digital Art": {
            "styles": ["Pixel perfect", "Modern", "Technological"],
            "color_mood": "Digital spectrum",
            "lighting": "Digital lighting",
            "enhancement": "pixel art, digital effects, screen glow, technological precision"
        },
        "Mixed Media": {
            "styles": ["Eclectic", "Layered", "Experimental"],
            "color_mood": "Mixed materials",
            "lighting": "Varied",
            "enhancement": "collage elements, texture mixing, material diversity, experimental techniques"
        },
        "Collage": {
            "styles": ["Assembled", "Fragmented", "Layered"],
            "color_mood": "Collage mix",
            "lighting": "Layered lighting",
            "enhancement": "cut paper, layered elements, fragmented composition, assembled materials"
        },
        "Photography": {
            "styles": ["Realistic", "Captured", "Documentary"],
            "color_mood": "Photographic",
            "lighting": "Natural photography",
            "enhancement": "lens effects, depth of field, photographic realism, captured moments"
        },
        "Illustration": {
            "styles": ["Drawn", "Stylized", "Narrative"],
            "color_mood": "Illustration palette",
            "lighting": "Illustrated",
            "enhancement": "hand-drawn quality, stylized forms, narrative elements, illustrative charm"
        },
        "Sculpture": {
            "styles": ["Three-dimensional", "Tactile", "Form"],
            "color_mood": "Material colors",
            "lighting": "Sculptural",
            "enhancement": "dimensional form, material texture, sculptural presence, physical weight"
        },
        "Architecture": {
            "styles": ["Structural", "Monumental", "Functional"],
            "color_mood": "Architectural materials",
            "lighting": "Architectural",
            "enhancement": "structural elements, building forms, architectural details, spatial relationships"
        },
        "Typography": {
            "styles": ["Textual", "Graphic", "Communicative"],
            "color_mood": "Type colors",
            "lighting": "Typographic",
            "enhancement": "letterforms, text layout, typographic hierarchy, graphic communication"
        },
        "Fairy Tale": {
            "styles": ["Whimsical", "Magical", "Storybook"],
            "color_mood": "Fairy tale palette",
            "lighting": "Magical",
            "enhancement": "enchanted forests, fairy tale castles, magical creatures, storybook charm"
        },
        "Horror": {
            "styles": ["Dark", "Frightening", "Ominous"],
            "color_mood": "Horror palette",
            "lighting": "Ominous shadows",
            "enhancement": "dark shadows, ominous atmosphere, frightening elements, horror mood"
        },
        "Sci-Fi": {
            "styles": ["Futuristic", "Technological", "Alien"],
            "color_mood": "Futuristic colors",
            "lighting": "Sci-fi lighting",
            "enhancement": "alien worlds, futuristic technology, space age design, science fiction elements"
        },
        "Western": {
            "styles": ["Frontier", "Rugged", "American"],
            "color_mood": "Desert and leather",
            "lighting": "Desert sun",
            "enhancement": "desert landscapes, cowboy imagery, frontier towns, western atmosphere"
        },
        "Adventure": {
            "styles": ["Dynamic", "Heroic", "Exciting"],
            "color_mood": "Adventure colors",
            "lighting": "Adventure lighting",
            "enhancement": "heroic poses, exciting action, dynamic movement, adventure spirit"
        },
        "Romance": {
            "styles": ["Tender", "Passionate", "Intimate"],
            "color_mood": "Romantic hues",
            "lighting": "Romantic",
            "enhancement": "tender moments, passionate embraces, intimate settings, romantic atmosphere"
        },
        "Thriller": {
            "styles": ["Suspenseful", "Tense", "Dramatic"],
            "color_mood": "Thriller palette",
            "lighting": "Suspenseful",
            "enhancement": "dramatic tension, suspenseful atmosphere, thriller elements, edge-of-seat mood"
        },
        "Comedy": {
            "styles": ["Light", "Humorous", "Playful"],
            "color_mood": "Bright and cheerful",
            "lighting": "Comedy lighting",
            "enhancement": "humorous elements, playful atmosphere, comedy timing, lighthearted mood"
        },
        "Drama": {
            "styles": ["Emotional", "Serious", "Character-driven"],
            "color_mood": "Dramatic colors",
            "lighting": "Dramatic",
            "enhancement": "emotional depth, character focus, dramatic moments, serious themes"
        },
        "Documentary": {
            "styles": ["Realistic", "Informative", "Truth-seeking"],
            "color_mood": "Documentary realism",
            "lighting": "Natural documentary",
            "enhancement": "realistic portrayal, documentary style, truthful representation, informative content"
        },
        "Ancient": {
            "styles": ["Historical", "Timeless", "Primitive"],
            "color_mood": "Ancient pigments",
            "lighting": "Ancient light",
            "enhancement": "ancient artifacts, historical elements, timeless quality, primitive beauty"
        },
        "Medieval": {
            "styles": ["Gothic", "Feudal", "Illuminated"],
            "color_mood": "Medieval colors",
            "lighting": "Medieval",
            "enhancement": "castle architecture, illuminated manuscripts, feudal imagery, medieval atmosphere"
        },
        "Victorian": {
            "styles": ["Ornate", "Industrial", "Proper"],
            "color_mood": "Victorian palette",
            "lighting": "Gas light",
            "enhancement": "ornate decoration, industrial elements, Victorian propriety, period atmosphere"
        },
        "Art Nouveau": {
            "styles": ["Flowing", "Natural", "Decorative"],
            "color_mood": "Art nouveau colors",
            "lighting": "Art nouveau",
            "enhancement": "flowing lines, natural motifs, decorative elements, art nouveau elegance"
        },
        "Bauhaus": {
            "styles": ["Functional", "Geometric", "Modern"],
            "color_mood": "Bauhaus primaries",
            "lighting": "Functional",
            "enhancement": "functional design, geometric forms, modern principles, bauhaus aesthetics"
        },
        "Impressionist": {
            "styles": ["Light-focused", "Atmospheric", "Momentary"],
            "color_mood": "Impressionist palette",
            "lighting": "Changing light",
            "enhancement": "broken brushstrokes, light effects, atmospheric mood, momentary impressions"
        },
        "Expressionist": {
            "styles": ["Emotional", "Distorted", "Subjective"],
            "color_mood": "Expressive colors",
            "lighting": "Expressionist",
            "enhancement": "emotional distortion, subjective reality, expressive brushwork, inner feelings"
        },
        "Cubist": {
            "styles": ["Fragmented", "Geometric", "Multi-perspective"],
            "color_mood": "Cubist palette",
            "lighting": "Fragmented",
            "enhancement": "geometric fragmentation, multiple perspectives, cubist analysis, abstract representation"
        },
        "Dadaist": {
            "styles": ["Anti-art", "Chaotic", "Rebellious"],
            "color_mood": "Dada chaos",
            "lighting": "Anti-traditional",
            "enhancement": "chaotic elements, anti-art sentiment, rebellious spirit, dada absurdity"
        },
        "Futurist": {
            "styles": ["Dynamic", "Speed", "Technology"],
            "color_mood": "Futurist energy",
            "lighting": "Dynamic",
            "enhancement": "speed lines, dynamic movement, technological progress, futurist energy"
        },
        "Constructivist": {
            "styles": ["Revolutionary", "Geometric", "Utilitarian"],
            "color_mood": "Revolutionary colors",
            "lighting": "Constructivist",
            "enhancement": "revolutionary spirit, geometric construction, utilitarian design, social purpose"
        },
        "Surrealist": {
            "styles": ["Dream logic", "Unconscious", "Fantastic"],
            "color_mood": "Surreal colors",
            "lighting": "Surreal",
            "enhancement": "dream imagery, unconscious symbols, fantastic elements, surreal juxtapositions"
        },
        "Abstract Expressionist": {
            "styles": ["Gestural", "Color field", "Emotional"],
            "color_mood": "Abstract expression",
            "lighting": "Emotional",
            "enhancement": "gestural brushwork, color field painting, emotional abstraction, expressive freedom"
        },
        "Pop": {
            "styles": ["Commercial", "Mass culture", "Repetitive"],
            "color_mood": "Pop art brights",
            "lighting": "Pop lighting",
            "enhancement": "commercial imagery, mass culture references, repetitive patterns, pop art aesthetics"
        },
        "Minimalist Movement": {
            "styles": ["Reduced", "Essential", "Pure"],
            "color_mood": "Minimal palette",
            "lighting": "Pure lighting",
            "enhancement": "essential elements, reduced forms, pure composition, minimalist philosophy"
        },
        "Japanese": {
            "styles": ["Zen", "Natural", "Asymmetrical"],
            "color_mood": "Japanese traditional",
            "lighting": "Japanese aesthetic",
            "enhancement": "zen philosophy, natural elements, asymmetrical balance, japanese aesthetics"
        },
        "Chinese": {
            "styles": ["Calligraphic", "Symbolic", "Harmonious"],
            "color_mood": "Chinese traditional",
            "lighting": "Chinese style",
            "enhancement": "calligraphy elements, symbolic imagery, harmonious composition, chinese culture"
        },
        "Indian": {
            "styles": ["Ornate", "Spiritual", "Colorful"],
            "color_mood": "Indian vibrant",
            "lighting": "Indian traditional",
            "enhancement": "ornate patterns, spiritual symbols, vibrant colors, indian cultural elements"
        },
        "African": {
            "styles": ["Tribal", "Rhythmic", "Earth-connected"],
            "color_mood": "African earth tones",
            "lighting": "African light",
            "enhancement": "tribal patterns, rhythmic elements, earth connection, african cultural motifs"
        },
        "Native American": {
            "styles": ["Spiritual", "Natural", "Symbolic"],
            "color_mood": "Natural earth colors",
            "lighting": "Natural spiritual",
            "enhancement": "spiritual symbols, natural harmony, cultural patterns, native american elements"
        },
        "Scandinavian": {
            "styles": ["Clean", "Functional", "Light"],
            "color_mood": "Nordic palette",
            "lighting": "Nordic light",
            "enhancement": "clean lines, functional beauty, light woods, scandinavian design"
        },
        "Mediterranean": {
            "styles": ["Warm", "Coastal", "Relaxed"],
            "color_mood": "Mediterranean blues",
            "lighting": "Mediterranean sun",
            "enhancement": "coastal views, warm atmosphere, relaxed lifestyle, mediterranean charm"
        },
        "Middle Eastern": {
            "styles": ["Ornate", "Geometric", "Luxurious"],
            "color_mood": "Middle eastern rich",
            "lighting": "Desert golden",
            "enhancement": "geometric patterns, ornate details, luxurious materials, middle eastern culture"
        },
        "Latin American": {
            "styles": ["Vibrant", "Festive", "Passionate"],
            "color_mood": "Latin american bright",
            "lighting": "Festive lighting",
            "enhancement": "vibrant festivals, passionate colors, cultural celebration, latin american spirit"
        },
        "European": {
            "styles": ["Classical", "Refined", "Historical"],
            "color_mood": "European sophistication",
            "lighting": "European classical",
            "enhancement": "classical architecture, refined culture, historical depth, european elegance"
        },
        "Morning Mist": {
            "styles": ["Soft", "Ethereal", "Fresh"],
            "color_mood": "Misty pastels",
            "lighting": "Dawn light",
            "enhancement": "morning fog, soft light, fresh air, misty atmosphere, new beginnings"
        },
        "Afternoon Sun": {
            "styles": ["Warm", "Bright", "Clear"],
            "color_mood": "Sunny yellows",
            "lighting": "Afternoon sun",
            "enhancement": "bright sunlight, warm shadows, clear skies, afternoon energy"
        },
        "Evening Glow": {
            "styles": ["Warm", "Romantic", "Peaceful"],
            "color_mood": "Evening warmth",
            "lighting": "Golden hour",
            "enhancement": "golden light, peaceful atmosphere, romantic glow, evening tranquility"
        },
        "Midnight Blue": {
            "styles": ["Deep", "Mysterious", "Calm"],
            "color_mood": "Deep blues",
            "lighting": "Moonlight",
            "enhancement": "deep night sky, mysterious shadows, calm stillness, midnight serenity"
        },
        "Dawn Light": {
            "styles": ["Fresh", "Hopeful", "Gentle"],
            "color_mood": "Dawn colors",
            "lighting": "First light",
            "enhancement": "first light, gentle awakening, hopeful atmosphere, dawn freshness"
        },
        "Melancholic": {
            "styles": ["Wistful", "Bittersweet", "Reflective"],
            "color_mood": "Melancholic tones",
            "lighting": "Soft melancholy",
            "enhancement": "wistful atmosphere, bittersweet memories, reflective mood, gentle sadness"
        },
        "Whimsical": {
            "styles": ["Playful", "Imaginative", "Childlike"],
            "color_mood": "Whimsical colors",
            "lighting": "Playful",
            "enhancement": "playful elements, imaginative details, childlike wonder, whimsical charm"
        }
    }

    
    # Apply preset button
    if mood_preset != "Custom" and mood_preset in MOOD_PRESETS:
        if st.button(f"✨ Apply {mood_preset} Preset", use_container_width=True):
            st.session_state.preset_applied = MOOD_PRESETS[mood_preset]
            st.session_state.preset_applied["mood"] = mood_preset
            st.success(f"{mood_preset} preset applied!")
            st.rerun()
    
    # Show applied preset info
    if hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied:
        st.info(f"🎭 Using: {st.session_state.preset_applied['mood']} preset")
    
    st.markdown("---")

    
    # Image Gallery
    if st.session_state.images:
        st.markdown("### ⭐ Your Gallery")

        # --- ADVANCED GALLERY CONTROLS ---
        with st.container(border=True):
            st.markdown("##### 🔬 Filter & Sort")
            
            # 1. Search Bar
            search_query = st.text_input(
                "🔍 Search by Prompt",
                placeholder="e.g., dragon, crystal, forest...",
                key="gallery_search"
            )
            
            # 2. Filter by Style
            # Get a unique, sorted list of styles used in the gallery
            all_styles_in_gallery = sorted(list(set(
                img.get('style_used', 'N/A') for img in st.session_state.images
            )))
            selected_styles_filter = st.multiselect(
                "🎨 Filter by Style",
                options=all_styles_in_gallery,
                key="gallery_style_filter"
            )
            
            # 3. Sort Order
            sort_order = st.selectbox(
                "⏳ Sort by",
                ["Newest First", "Oldest First"],
                key="gallery_sort"
            )

        # --- FILTERING AND SORTING LOGIC ---
        
        # Start with all images and apply filters sequentially
        filtered_images = st.session_state.images
        
        # Apply search query filter
        if search_query:
            filtered_images = [
                img for img in filtered_images
                if search_query.lower() in img.get('original_prompt', '').lower() or \
                   search_query.lower() in img.get('enhanced_prompt', '').lower()
            ]
            
        # Apply style filter
        if selected_styles_filter:
            filtered_images = [
                img for img in filtered_images
                if img.get('style_used') in selected_styles_filter
            ]
            
        # Apply sorting
        # Note: New images are appended, so the default list is "Oldest First"
        if sort_order == "Newest First":
            # Create a reversed copy for display
            display_list = list(reversed(filtered_images))
        else: # "Oldest First"
            display_list = filtered_images

        st.markdown("---")

        # --- DISPLAY FILTERED GALLERY ---
        
        # Show how many results were found
        st.markdown(f"**{len(display_list)}** image(s) found.")

        if not display_list:
            st.info("No images match your current filter criteria.")
        else:
            # Display thumbnail gallery
            for i, img_data in enumerate(display_list):
                img_id = img_data['id']
                with st.container():
                    # Main container for image and buttons
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        img = Image.open(BytesIO(img_data['image_data']))
                        img.thumbnail((80, 80))
                        st.image(img, use_container_width=True)
                    
                    with col2:
                        prompt_summary = img_data.get('original_prompt', 'No Prompt')[:50]
                        st.markdown(f"<small>*{prompt_summary}...*</small>", unsafe_allow_html=True)
                        
                        # Columns for View and Remove buttons
                        view_col, remove_col = st.columns([3, 1])
                        with view_col:
                            if st.button(f"{i}", key=f"view_{img_id}", use_container_width=True):
                                st.session_state.current_image = img_data
                                st.rerun()
                        with remove_col:
                            st.button(
                                "🗑️", 
                                key=f"remove_gallery_{img_id}", 
                                on_click=remove_image_from_gallery, 
                                args=(img_id,), 
                                use_container_width=True, 
                                help="Remove image permanently"
                            )

        st.markdown("---")

        # Clear gallery button remains at the end
        if st.button("🗑️ Clear Entire Gallery", use_container_width=True):
            st.session_state.images = []
            st.session_state.current_image = None
            st.session_state.favorites = [] # Also clear favorites
            st.session_state.prompt_history = [] # Also clear history
            st.rerun()
            
        st.markdown("---")
                        
        st.markdown("---")        

# Main content area
col1, col2 = st.columns([2, 1])
with col1:
    # Enhanced prompt input
    st.markdown("### 🖋️ Describe Your Vision")
    prompt = st.text_area(
        "Enter your creative prompt:",
        height=100,
        placeholder="A majestic dragon soaring through a crystal cave filled with glowing gems...",
        help="Be descriptive! Include details about subjects, settings, mood, and style.",
        key="main_prompt"
    )
        # >>> ADD THIS CODE BLOCK <<<
    negative_prompt = st.text_area(
        "🚫 Negative Prompt (Optional)",
        height=80,
        placeholder="e.g., blurry, ugly, text, watermark, extra limbs, bad anatomy...",
        help="Tell the AI what to AVOID in the image. Separate concepts with commas.",
        key="negative_prompt_input"
    )
    # >>> END OF CODE BLOCK <<<
    
    # Prompt enhancement options
    enhance_prompt = st.checkbox(" 🦄 Auto-enhance prompt with selected styles", key="enhance_check")
    
    # Generate button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        if st.button("✨ Generate Masterpiece", key="generate_btn", use_container_width=True):
            if not prompt.strip():
                st.markdown('<div class="error-box">❌ Please enter a prompt to begin your creative journey!</div>', unsafe_allow_html=True)
            else:
                # Enhance prompt if requested or preset applied
                if enhance_prompt or (hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied):
                    if hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied:
                        preset = st.session_state.preset_applied
                        enhanced_prompt = f"{prompt}, {preset['styles'][0]} style, {preset['color_mood']} color palette, {preset['lighting']} lighting, {preset['enhancement']}, {quality_level} quality"
                    else:
                        enhanced_prompt = f"{prompt}, {selected_style} style, {color_mood} color palette, {lighting} lighting, {quality_level} quality"
                else:
                    enhanced_prompt = prompt

                # --- ADDED: Step 2 - Add the new prompt to history ---
                if enhanced_prompt not in st.session_state.prompt_history:
                    st.session_state.prompt_history.insert(0, enhanced_prompt)
                    save_prompt_history_to_db()
                # ---

                # Show enhanced prompt
                if enhance_prompt or (hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied):
                    st.markdown("**Enhanced Prompt:**")
                    st.code(enhanced_prompt, language=None)

                # Progress indicators
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                # --- START: API KEY ROTATION LOGIC ---
                generation_successful = False
                max_retries = len(st.secrets.get("gemini_api_keys", []))
                
                for attempt in range(max_retries):
                    try:
                        # Use a local client variable that gets re-initialized on retry
                        local_client = initialize_gemini_client()

                        status_text.text(f"🎨 Initializing... (Using Key {st.session_state.current_api_key_index + 1})")
                        progress_bar.progress(20)
                        
                        status_text.text("✨ Creating your masterpiece...")
                        progress_bar.progress(60)
                        
                        generation_contents = [enhanced_prompt]
                        if negative_prompt:
                            generation_contents.append(f"Negative prompt: {negative_prompt}")

                        response = local_client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=generation_contents,
                            config=types.GenerateContentConfig(
                                response_modalities=["text", "image"]
                            )
                        )
                        
                        progress_bar.progress(100)
                        status_text.text("🎉 Masterpiece complete!")
                        
                        image_data, description = None, ""
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                description = part.text
                            elif part.inline_data:
                                image_data = part.inline_data.data
                        
                        if image_data:
                            generation_successful = True
                            image_metadata = {
                                'id': str(uuid.uuid4()),
                                'image_data': image_data,
                                'original_prompt': prompt,
                                'enhanced_prompt': enhanced_prompt,
                                'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                                'style_used': selected_style,
                                'color_mood': color_mood,
                                'lighting': lighting,
                                'description': description,
                                'aspect_ratio': aspect_ratio,
                                'quality_level': quality_level
                            }
                            st.session_state.images.append(image_metadata)
                            save_image_to_db(image_metadata)
                            st.session_state.current_image = image_metadata
                            
                            progress_container.empty()
                            st.markdown('<div class="success-box">🎉 Your masterpiece has been created!</div>', unsafe_allow_html=True)
                            st.rerun()
                        else:
                             st.markdown('<div class="error-box">❌ No image was generated. Please try again with a different prompt.</div>', unsafe_allow_html=True)
                        break  # Exit loop on success

                    except Exception as e:
                        error_msg = str(e).lower()
                        if "quota" in error_msg or "limit" in error_msg:
                            if st.session_state.current_api_key_index < max_retries - 1:
                                rotate_api_key()
                                continue  # Retry with the next key
                            else:
                                st.markdown('<div class="error-box">⏳ All API keys have reached their limit. Please try again later.</div>', unsafe_allow_html=True)
                                break
                        else:
                            # Handle other errors like safety, network, etc.
                            if "api key" in error_msg or "authentication" in error_msg:
                                st.markdown('<div class="error-box">🔑 Authentication Error: Please check your API key configuration.</div>', unsafe_allow_html=True)
                            elif "safety" in error_msg or "policy" in error_msg:
                                st.markdown('<div class="error-box">🛡️ Content Policy: Your prompt may violate guidelines. Please try a different description.</div>', unsafe_allow_html=True)
                            elif "network" in error_msg or "connection" in error_msg:
                                st.markdown('<div class="error-box">🌐 Network Error: Please check your internet connection and try again.</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-box">⚠️ Generation Error: {str(e)}</div>', unsafe_allow_html=True)
                            break # Exit loop for other errors

                if not generation_successful:
                    progress_container.empty()
                # --- END: API KEY ROTATION LOGIC ---
                    



                    

    # Display current image
    if st.session_state.current_image:
        st.markdown("---")
        img_data = st.session_state.current_image
        img = Image.open(BytesIO(img_data['image_data']))
        
        st.image(img, caption="✨ Generated Masterpiece", use_container_width=True)
        # vvvvv  ADD THIS BLOCK FOR THE FAVORITE BUTTON  vvvvv
        def toggle_favorite(image_id):
            if image_id in st.session_state.favorites:
                st.session_state.favorites.remove(image_id)
                st.toast("💔 Removed from favorites.")
            else:
                st.session_state.favorites.append(image_id)
                st.toast("⭐ Added to favorites!")

            save_favorites_to_db()

        
                

        

        # Use a filled or empty star for visual feedback
        is_favorited = img_data['id'] in st.session_state.favorites
        star_icon = "★" if is_favorited else "☆"
        
        st.button(
            f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", 
            on_click=toggle_and_save_favorite, 
            args=(img_data['id'],),
            use_container_width=True
        )
        # ^^^^^  END OF FAVORITE BUTTON BLOCK  ^^^^^


        
        # --- START: GENERATE VARIATION FEATURE (SINGLE) ---
        with st.container(border=True):
            if st.button("🎨 Create Variation", use_container_width=True, type="primary"):
                with st.spinner("summoning a new masterpiece..."):
                    
                    newly_generated = []
                    try:
                        original_image_pil = Image.open(BytesIO(img_data['image_data']))
                        original_prompt_text = img_data.get('enhanced_prompt', img_data.get('original_prompt', ''))
                        
                        variation_prompt = (
                            f"Generate a new, unique variation of the provided image. The original concept was: '{original_prompt_text}'. "
                            "Maintain the core subject and theme, but creatively alter the composition, lighting, or details to offer a fresh perspective."
                        )

                        # --- CORRECTED CODE ---
                        # Build the contents list for the API call
                        variation_contents = [variation_prompt, original_image_pil]

                        # Add the negative prompt if it exists from the main input
                        if negative_prompt:
                             variation_contents.append(f"Negative prompt: {negative_prompt}")
                        
                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=variation_contents, # Use the new list here
                            config=types.GenerateContentConfig(
                                response_modalities=["text", "image"]
                            )
                        )
                        # --- END OF CORRECTION ---

                        new_image_data = None
                        new_description = ""
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                new_description = part.text
                            elif part.inline_data:
                                new_image_data = part.inline_data.data
                        
                        if new_image_data:
                            new_image_metadata = {
                                'id': str(uuid.uuid4()), 'image_data': new_image_data,
                                'original_prompt': f"Variation of: {img_data['original_prompt']}",
                                'enhanced_prompt': variation_prompt, 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                                'style_used': img_data.get('style_used'), 'color_mood': img_data.get('color_mood'),
                                'lighting': img_data.get('lighting'), 'description': new_description,
                                'aspect_ratio': img_data.get('aspect_ratio'), 'quality_level': img_data.get('quality_level')
                            }
                            st.session_state.images.append(new_image_metadata)
                            save_image_to_db(new_image_metadata)
                            newly_generated.append(new_image_metadata)
                    
                        st.session_state.newly_generated_variations = newly_generated
                        st.success("Successfully created a new variation!")

                    except Exception as e:
                        st.error(f"Failed to generate a variation: {e}")
        # --- END: GENERATE VARIATION FEATURE (SINGLE) ---

        # --- START: DISPLAY NEW VARIATION ---
        # --- START: DISPLAY NEW VARIATION ---

        st.markdown("---")
        # Description if available
        if img_data.get('description'):
            st.markdown("### 📝 AI Description")
            st.info(img_data['description'])
                        # --- START: ADD THIS CODE BLOCK FOR TEXT-TO-SPEECH ---
            try:
                # Create an in-memory audio buffer
                audio_buffer = BytesIO()

                # Generate the speech using gTTS
                tts = gTTS(text=img_data['description'], lang='en', slow=False)
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)

                # Display the audio player in Streamlit
                st.audio(audio_buffer, format='audio/mp3', start_time=0)

            except Exception as e:
                st.warning(f"Could not generate audio for the description. Error: {e}")
            # --- END: ADD THIS CODE BLOCK ---
        
        # Download section
        st.markdown("### 💾 Export Your Masterpiece")
        
        download_col1, download_col2, download_col3, download_col4 = st.columns(4)
        
        # PNG download
        with download_col1:
            png_buffer = BytesIO()
            img.save(png_buffer, format="PNG", optimize=True)
            st.download_button(
                "📥 PNG",
                data=png_buffer.getvalue(),
                file_name=f"genai_masterpiece_{int(time.time())}.png",
                mime="image/png",
                key=f"png_{img_data['id']}",
                use_container_width=True
            )
        
        # JPEG download
        with download_col2:
            jpg_buffer = BytesIO()
            if img.mode == 'RGBA':
                jpg_img = Image.new('RGB', img.size, (255, 255, 255))
                jpg_img.paste(img, mask=img.split()[-1])
            else:
                jpg_img = img
            jpg_img.save(jpg_buffer, format="JPEG", quality=95, optimize=True)
            st.download_button(
                "📥 JPG",
                data=jpg_buffer.getvalue(),
                file_name=f"genai_masterpiece_{int(time.time())}.jpg",
                mime="image/jpeg",
                key=f"jpg_{img_data['id']}",
                use_container_width=True
            )
        
        # WebP download
        with download_col3:
            webp_buffer = BytesIO()
            img.save(webp_buffer, format="WEBP", quality=90, optimize=True)
            st.download_button(
                "📥 WebP",
                data=webp_buffer.getvalue(),
                file_name=f"genai_masterpiece_{int(time.time())}.webp",
                mime="image/webp",
                key=f"webp_{img_data['id']}",
                use_container_width=True
            )
        
        # Metadata download
        with download_col4:
            metadata = {k: v for k, v in img_data.items() if k != 'image_data'}
            st.download_button(
                "📄 Info",
                data=json.dumps(metadata, indent=2),
                file_name=f"genai_metadata_{int(time.time())}.json",
                mime="application/json",
                key=f"json_{img_data['id']}",
                use_container_width=True
            )
        
        # Image info
        st.markdown(f"""
        <div class="download-container">
        <strong>📊 Image Details:</strong><br>
        • Size: {img.size[0]} × {img.size[1]} pixels<br>
        • Format: {img.format}<br>
        • Mode: {img.mode}<br>
        • Generated: {img_data['generation_time']}
        </div>
        """, unsafe_allow_html=True)

        
                # --- START: DISPLAY NEW VARIATION ---
        if 'newly_generated_variations' in st.session_state and st.session_state.newly_generated_variations:
            st.markdown("---")
            st.markdown("### ✨ Your New Variation")
            
            # Since there's only one, we access it directly
            variation_data = st.session_state.newly_generated_variations[0]
            
            st.image(
                variation_data['image_data'], 
                caption="New Variation", 
                use_container_width=True
            )

                        # --- FAVORITE BUTTON FOR VARIATION ---
            def toggle_favorite_variation(image_id):
                if image_id in st.session_state.favorites:
                    st.session_state.favorites.remove(image_id)
                else:
                    st.session_state.favorites.append(image_id)

            is_favorited_var = variation_data['id'] in st.session_state.favorites
            star_icon_var = "★" if is_favorited_var else "☆"
            
            st.button(
                f"{star_icon_var} {'Favorited' if is_favorited_var else 'Favorite'}", 
                on_click=toggle_and_save_favorite,
                args=(variation_data['id'],),
                key=f"fav_btn_variation_{variation_data['id']}",
                use_container_width=True
            )
            # --- START: AI DESCRIPTION FOR VARIATION ---
                        # --- AI DESCRIPTION FOR VARIATION ---
            if variation_data.get('description'):
                st.markdown("### 📝 AI Description (Variation)")
                st.info(variation_data['description'])

                # --- ADDED: Text-to-speech for Variation Description ---
                try:
                    audio_buffer_var = BytesIO()
                    tts_var = gTTS(text=variation_data['description'], lang='en', slow=False)
                    tts_var.write_to_fp(audio_buffer_var)
                    audio_buffer_var.seek(0)
                    st.audio(audio_buffer_var, format='audio/mp3', start_time=0)
                except Exception as e:
                    st.warning(f"Could not generate audio for the variation description. Error: {e}")

            # --- START: EXPORT BUTTONS FOR VARIATION ---
                        # --- START: EXPORT BUTTONS FOR VARIATION ---
            st.markdown("### 💾 Export Your Variation Masterpiece")
            
            # Open the image data once for reuse
            variation_img = Image.open(BytesIO(variation_data['image_data']))
            
            # Create four columns for the buttons
            dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)

            # PNG download
            with dl_col1:
                png_buffer = BytesIO()
                variation_img.save(png_buffer, format="PNG", optimize=True)
                st.download_button(
                    label="📥 PNG",
                    data=png_buffer.getvalue(),
                    file_name=f"variation_{int(time.time())}.png",
                    mime="image/png",
                    key=f"dl_var_png_{variation_data['id']}",
                    use_container_width=True
                )

            # JPG download
            with dl_col2:
                jpg_buffer = BytesIO()
                # Handle transparency for JPG conversion
                if variation_img.mode == 'RGBA':
                    jpg_img = Image.new('RGB', variation_img.size, (255, 255, 255))
                    jpg_img.paste(variation_img, mask=variation_img.split()[-1])
                else:
                    jpg_img = variation_img
                jpg_img.save(jpg_buffer, format="JPEG", quality=95, optimize=True)
                st.download_button(
                    label="📥 JPG",
                    data=jpg_buffer.getvalue(),
                    file_name=f"variation_{int(time.time())}.jpg",
                    mime="image/jpeg",
                    key=f"dl_var_jpg_{variation_data['id']}",
                    use_container_width=True
                )

            # WebP download
            with dl_col3:
                webp_buffer = BytesIO()
                variation_img.save(webp_buffer, format="WEBP", quality=90, optimize=True)
                st.download_button(
                    label="📥 WebP",
                    data=webp_buffer.getvalue(),
                    file_name=f"variation_{int(time.time())}.webp",
                    mime="image/webp",
                    key=f"dl_var_webp_{variation_data['id']}",
                    use_container_width=True
                )
        
            # Metadata download
            with dl_col4:
                # Exclude the raw image data from the JSON file
                metadata = {k: v for k, v in variation_data.items() if k != 'image_data'}
                st.download_button(
                    label="📄 Info",
                    data=json.dumps(metadata, indent=2),
                    file_name=f"variation_metadata_{int(time.time())}.json",
                    mime="application/json",
                    key=f"dl_var_json_{variation_data['id']}",
                    use_container_width=True
                )
                        # --- ADDED: Image Details for Variation ---
            st.markdown(f"""
            <div class="download-container">
            <strong>📊 Image Details:</strong><br>
            • Size: {variation_img.size[0]} × {variation_img.size[1]} pixels<br>
            • Format: {variation_img.format or 'N/A'}<br>
            • Mode: {variation_img.mode}<br>
            • Generated: {variation_data['generation_time']}
            </div>
            """, unsafe_allow_html=True)
            # --- END: EXPORT BUTTONS FOR VARIATION ---
            # --- END: EXPORT BUTTONS FOR VARIATION ---




            


        # --- END: DISPLAY NEW VARIATION ---

with col2:
    st.markdown("### 💡 Quick Tips")

    tip_options = {
        "--- Select a Tip ---": "Select a category from the dropdown to learn more about crafting the perfect prompt.",
        "✍️ Effective Prompting 101": """
        A great prompt is a recipe for a great image. Structure your ideas clearly for the best results.
        - **Subject**: Start with the main focus. *'A majestic lion', 'A futuristic city', 'A portrait of a queen'.*
        - **Medium**: How was it made? *'Oil painting', 'Photograph', '3D render', 'Pencil sketch'.*
        - **Style**: The artistic influence. *'Impressionism', 'Cyberpunk', 'Art Nouveau', 'by Van Gogh'.*
        - **Setting & Context**: Where and when? *'in a sun-drenched meadow', 'on a distant alien planet', 'during the Roaring Twenties'.*
        - **Composition**: How is it framed? *'Wide-angle shot', 'Close-up portrait', 'Bird's-eye view'.*
        - **Lighting**: How is it lit? *'Soft morning light', 'Dramatic cinematic lighting', 'Neon glow'.*
        - **Color & Mood**: The emotional tone. *'Vibrant and energetic', 'Monochromatic and somber', 'Pastel and dreamy'.*
        
        **Example Breakdown:**
        `A photorealistic close-up portrait of an old wizard, in the style of Rembrandt, dramatic studio lighting, deep shadows, intricate wrinkles, wise expression, 8k`
        """,
        "🖼️ Composition & Framing": """
        Control the virtual camera to frame your subject perfectly.
        - **`Wide-angle shot`, `Panoramic`**: Captures a broad scene, great for landscapes.
        - **`Close-up`, `Macro shot`**: Focuses on small details.
        - **`Portrait`, `Full-body shot`**: Specifies how much of a character is visible.
        - **`Bird's-eye view`, `Top-down view`**: Looks directly down on the scene.
        - **`Low-angle shot`, `Worm's-eye view`**: Looks up from below, making subjects seem powerful.
        - **`Dutch angle`, `Tilted frame`**: Creates a sense of unease or dynamism.
        - **`Rule of thirds`**: A classic composition technique for balanced images.
        """,
        "🔑 Understanding Keywords": """
        Certain words act as powerful modifiers. Use them to guide the AI.
        - **Quality Boosters**: `masterpiece`, `best quality`, `highly detailed`, `intricate details`, `4k`, `8k`, `UHD`. These encourage the AI to spend more effort on detail.
        - **Realism**: `photorealistic`, `realistic`, `DSLR photo`, `shot on film`.
        - **Artistic Mediums**: `oil painting`, `watercolor`, `charcoal sketch`, `digital art`, `sculpture`.
        - **Rendering Engines**: For digital art, try `Unreal Engine`, `Octane render`, `V-Ray` to simulate specific 3D rendering styles.
        """,
        "🎨 Blending Artist Styles": """
        Create unique aesthetics by combining influences.
        - **Simple Blend**: *'A cat, in the style of Van Gogh and Hayao Miyazaki'.* The AI will try to merge the swirling brushstrokes of Van Gogh with the whimsical character design of Miyazaki.
        - **Weighted Blend**: You can sometimes influence the mix with parentheses, though this is model-dependent. *'A (Van Gogh:1.2) and (Miyazaki:0.8) style cat'.*
        - **Conceptual Blend**: Combine a subject with an unrelated artist's style for surprising results. *'A futuristic city skyline in the style of Claude Monet'.*
        """,
        "🚫 Mastering Negative Prompts": """
        Telling the AI what *not* to do is as important as telling it what to do. Use the Negative Prompt box to refine your results.
        - **Fix Common Flaws**: `ugly, deformed, disfigured, extra limbs, bad anatomy, blurry, grainy, text, watermark, signature`.
        - **Remove Unwanted Objects**: `no people, no cars, no buildings`.
        - **Control the Style**: If you want a photo, you might add `painting, drawing, illustration, cartoon` to the negative prompt.
        - **Refine Colors**: `monochrome, black and white, oversaturated`.
        """
    }

    selected_tip = st.selectbox(
        "Select a tip category:",
        options=list(tip_options.keys()),
        key="quick_tips_selector"
    )

    with st.container(border=True):
        st.markdown(tip_options[selected_tip])

    st.markdown("### 🛠️ Creative Utilities")

    # ... inside col2, after st.markdown("### 🛠️ Creative Utilities")

    # --- START: 4X UPSCALER TOOL ---
    with st.expander(" ♾️ Upscaler (4x) ", expanded=False):
        st.info("Increase the resolution of an image. This tool aims for a faithful 4x upscale without altering the original content.")
        
        upscaler_image = st.file_uploader(
            "Upload your image to upscale",
            type=["png", "jpg", "jpeg", "webp"],
            key="upscaler_uploader"
        )

        if upscaler_image:
            # When a new image is uploaded, clear the previous result
            if 'upscaler_img_bytes' not in st.session_state or upscaler_image.getvalue() != st.session_state.get('upscaler_img_bytes'):
                st.session_state.upscaler_img_bytes = upscaler_image.getvalue()
                st.session_state.upscaled_result_data = None

            original_pil_upscale = Image.open(BytesIO(st.session_state.upscaler_img_bytes))
            st.image(original_pil_upscale, caption=f"Original Image ({original_pil_upscale.size[0]}x{original_pil_upscale.size[1]})")

            if st.button(" ♾️ Generate Upscaled Image", use_container_width=True):
                with st.spinner("Performing high-resolution upscale... This may take a moment."):
                    try:
                        # This prompt is crucial for telling the model to *only* upscale
                        upscale_prompt = (
                            "Perform a 4x photorealistic upscale of the provided image. "
                            "It is critically important to not change the content, style, composition, or colors of the original image. "
                            "The output must be a very high contrast , high-resolution, high-detail, and faithful version of the original. "
                            "Do not add, remove, or alter any elements."
                        )

                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=[upscale_prompt, original_pil_upscale],
                            config=types.GenerateContentConfig(response_modalities=["text", "image"])
                        )
                        
                        st.session_state.upscaled_result_dict = None
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                st.session_state.upscaled_result_dict = {
                                    "id": str(uuid.uuid4()),
                                    "data": part.inline_data.data,
                                    "original_filename": upscaler_image.name
                                }
                                break



                        #if not st.session_state.upscaled_result_data:
                        #    st.error("The model did not return an upscaled image. Please try again.")
                           
                        
                           

                    except Exception as e:
                        st.error(f"Upscaling failed: {e}")

        # Display the upscaled result if it exists
        # Display the upscaled result if it exists
        if 'upscaled_result_dict' in st.session_state and st.session_state.upscaled_result_dict:
            st.markdown("---")
            st.markdown("#### ✨ Upscaled Result")

            result_dict = st.session_state.upscaled_result_dict
            upscaled_data = result_dict['data']
            image_id = result_dict['id']
            original_filename = result_dict.get('original_filename', f"image_{int(time.time())}.png")
            
            result_img_upscaled = Image.open(BytesIO(upscaled_data))
            
            st.image(result_img_upscaled, use_container_width=True, caption=f"Upscaled Image ({result_img_upscaled.size[0]}x{result_img_upscaled.size[1]})")
            
            st.download_button(
                label="📥 Download Upscaled Image",
                data=upscaled_data,
                file_name=f"upscaled_4x_{original_filename}",
                mime="image/png",
                use_container_width=True,
                key=f"download_upscaled_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_upscaled_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': upscaled_data,
                        'original_prompt': f"Upscaled: {original_filename}",
                        'enhanced_prompt': "Image created with the 4x Upscaler utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Upscaler', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image enhanced using the 4x Upscaler feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_upscaled_{image_id}"):
                    add_upscaled_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_upscaled():
                    add_upscaled_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_upscaled,
                    use_container_width=True,
                    key=f"fav_upscaled_{image_id}"
                )
    # --- END: 4X UPSCALER TOOL ---

    # The existing Outpainting expander should follow right after this block
    
    # --- START: INPAINTING (MAGIC ERASE) TOOL ---
# --- START: INPAINTING (MAGIC ERASE) TOOL ---
# --- START: INPAINTING (MAGIC ERASE) TOOL ---
# --- START: INPAINTING (MAGIC ERASE) TOOL ---
# --- START: INPAINTING (MAGIC ERASE) TOOL ---
# --- START: INPAINTING (MAGIC ERASE) TOOL ---
    with st.expander("🪄 Magic Erase & Edit", expanded=False):
        st.info("Magic edit using nano banana (gemini-2.5-flash-image) [Beta] ")

        inpainting_image_file = st.file_uploader(
            "Upload an image to edit",
            type=["png", "jpg", "jpeg", "webp"],
            key="inpainting_uploader"
        )

        if inpainting_image_file:
            if 'inpainting_img_bytes' not in st.session_state or inpainting_image_file.getvalue() != st.session_state.get('inpainting_img_bytes'):
                st.session_state.inpainting_img_bytes = inpainting_image_file.getvalue()
                st.session_state.inpainting_result_dict = None

            original_pil_inpainting = Image.open(BytesIO(st.session_state.inpainting_img_bytes))

            # --- FIX: Display the uploaded image before the canvas ---
            st.markdown("##### 1. Your Uploaded Image")
            st.image(original_pil_inpainting, caption="This is the image you'll be editing on the canvas below.", use_container_width=True)
            st.markdown("---")
            # --- END FIX ---

            st.markdown("##### 2. Describe Your Edit & Draw a Mask")
            inpainting_prompt = st.text_input("What should replace the masked area?", placeholder="e.g., a majestic eagle, a field of flowers, remove the person", key="inpainting_prompt_text")

            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0.5)",
                stroke_width=20,
                stroke_color="#FFFFFF",
                background_image=original_pil_inpainting,
                update_streamlit=True,
                height=original_pil_inpainting.height,
                width=original_pil_inpainting.width,
                drawing_mode="freedraw",
                key="inpainting_canvas",
            )

            if st.button("🪄 Perform Inpainting", use_container_width=True):
                if canvas_result.image_data is not None and inpainting_prompt:
                    with st.spinner("The AI is working its magic..."):
                        try:
                            # We still convert the original image to RGB here for the AI model
                            original_for_api = original_pil_inpainting.convert("RGB")
                            mask_pil = Image.fromarray(canvas_result.image_data).convert("L")
                            
                            inpaint_api_prompt = (
                                "You are an expert image editor. Use the provided mask to perform an inpainting task. "
                                f"Replace the masked (white) area with: '{inpainting_prompt}'. "
                                "Ensure the new content blends seamlessly with the original image in terms of style, lighting, and texture."
                            )
                            response = client.models.generate_content(
                                model="gemini-2.0-flash-exp-image-generation",
                                contents=[inpaint_api_prompt, original_for_api, mask_pil],
                                config=types.GenerateContentConfig(response_modalities=["text", "image"])
                            )
                            st.session_state.inpainting_result_dict = None
                            for part in response.candidates[0].content.parts:
                                if part.inline_data:
                                    st.session_state.inpainting_result_dict = {
                                        "id": str(uuid.uuid4()),
                                        "data": part.inline_data.data,
                                        "original_filename": inpainting_image_file.name
                                    }
                                    break
                            if not st.session_state.inpainting_result_dict:
                                st.error("The model did not return an edited image. Please try again.")
                        except Exception as e:
                            st.error(f"Inpainting failed: {e}")
                else:
                    st.warning("Please draw a mask on the image and provide a prompt.")

        if 'inpainting_result_dict' in st.session_state and st.session_state.inpainting_result_dict:
            st.markdown("---")
            st.markdown("#### ✨ Inpainting Result")
            result_dict = st.session_state.inpainting_result_dict
            result_data = result_dict['data']
            image_id = result_dict['id']
            original_filename = result_dict.get('original_filename', f"image_{int(time.time())}.png")
            st.image(result_data, use_container_width=True, caption="Your edited masterpiece")
            st.download_button(label="📥 Download Edited Image", data=result_data, file_name=f"inpainted_{original_filename}", mime="image/png", use_container_width=True, key=f"download_inpainted_{image_id}")
    # --- END: INPAINTING (MAGIC ERASE) TOOL ---



    with st.expander("↔️ Outpainting (Magic Expand)", expanded=False):

        st.info("Expand your image by adding new content around the edges, guided by a prompt.")
        
        outpainting_image = st.file_uploader(
            "Upload your source image",
            type=["png", "jpg", "jpeg", "webp"],
            key="outpainting_uploader"
        )

        if outpainting_image:
            # When a new image is uploaded, clear the previous result
            if 'outpainting_img_bytes' not in st.session_state or outpainting_image.getvalue() != st.session_state.get('outpainting_img_bytes'):
                st.session_state.outpainting_img_bytes = outpainting_image.getvalue()
                st.session_state.outpainting_result_dict = None

            original_pil = Image.open(BytesIO(st.session_state.outpainting_img_bytes))
            st.image(original_pil, caption="Original Image")

            outpainting_prompt = st.text_input("Describe what to add in the new space", placeholder="e.g., a beautiful starry sky, more of the forest...", key="outpainting_prompt_text")
            expand_percent = st.slider("Expansion Amount (%)", 10, 100, 50, key="outpainting_expand")
            
            cols = st.columns(2)
            expand_left = cols[0].checkbox("Left")
            expand_right = cols[1].checkbox("Right")
            expand_top = cols[0].checkbox("Top")
            expand_bottom = cols[1].checkbox("Bottom")
            
            if st.button("↔️ Generate Outpainting", use_container_width=True):
                if not any([expand_left, expand_right, expand_top, expand_bottom]):
                    st.warning("Please select at least one direction to expand.")
                else:
                    with st.spinner("Analyzing image and expanding canvas..."):
                        try:
                            # Analyze the original image to get its style
                            analysis_prompt = "In 10 words or less, describe the visual style of this image (e.g., 'vibrant anime style, sunset lighting'). Do not describe the content, only the style."
                            analysis_response = client.models.generate_content(
                                model="gemini-2.0-flash", 
                                contents=[analysis_prompt, original_pil]
                            )
                            image_style = analysis_response.candidates[0].content.parts[0].text.strip()
                            st.info(f"Detected Style: {image_style}")
                            
                            w, h = original_pil.size
                            new_w = w + (int(w * expand_percent / 100) if expand_left else 0) + (int(w * expand_percent / 100) if expand_right else 0)
                            new_h = h + (int(h * expand_percent / 100) if expand_top else 0) + (int(h * expand_percent / 100) if expand_bottom else 0)
                            new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
                            mask = Image.new('L', (new_w, new_h), 255)
                            paste_x = int(w * expand_percent / 100) if expand_left else 0
                            paste_y = int(h * expand_percent / 100) if expand_top else 0
                            new_img.paste(original_pil, (paste_x, paste_y))
                            mask.paste(0, (paste_x, paste_y, paste_x + w, paste_y + h))
                            
                            outpaint_api_prompt = (
                                "You are an expert image editor performing an outpainting task. "
                                f"Fill the white area of the mask with a seamless, logical extension of the original image, matching the detected style: '{image_style}'. "
                                f"The new content to add is: '{outpainting_prompt}'. Do not introduce clashing styles."
                            )

                            response = client.models.generate_content(
                                model="gemini-2.0-flash-exp-image-generation",
                                contents=[outpaint_api_prompt, new_img, mask],
                                config=types.GenerateContentConfig(response_modalities=["text", "image"])
                            )

                            st.session_state.outpainting_result_dict = None
                            for part in response.candidates[0].content.parts:
                                if part.inline_data:
                                    st.session_state.outpainting_result_dict = {
                                        "id": str(uuid.uuid4()),
                                        "image_data": part.inline_data.data,
                                        "prompt": outpainting_prompt,
                                        "style": image_style
                                    }
                                    break
                            
                            if not st.session_state.outpainting_result_dict:
                                st.error("The model did not return an image. Please try again.")

                        except Exception as e:
                            st.error(f"Outpainting failed: {e}")

        if 'outpainting_result_dict' in st.session_state and st.session_state.outpainting_result_dict:
            st.markdown("---")
            st.markdown("#### ✨ Outpainting Result")

            outpainted_data = st.session_state.outpainting_result_dict
            result_img = Image.open(BytesIO(outpainted_data['image_data']))
            
            st.image(result_img, use_container_width=True, caption="Your expanded masterpiece")
            
            st.download_button(
                label="📥 Download Outpainted Image",
                data=outpainted_data['image_data'],
                file_name="outpainted_image.png",
                mime="image/png",
                use_container_width=True
            )

            b_col1, b_col2 = st.columns(2)

            is_in_gallery = any(img['id'] == outpainted_data['id'] for img in st.session_state.images)

            def add_outpainted_to_gallery():
                if not any(img['id'] == outpainted_data['id'] for img in st.session_state.images):
                    gallery_metadata = {
                        'id': outpainted_data['id'],
                        'image_data': outpainted_data['image_data'],
                        'original_prompt': outpainted_data['prompt'],
                        'enhanced_prompt': f"Outpainted image using style: {outpainted_data['style']}",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': outpainted_data['style'],
                        'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created with the Outpainting (Magic Expand) feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == outpainted_data['id'] for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_outpainted_{outpainted_data['id']}"):
                    add_outpainted_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = outpainted_data['id'] in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                fav_text = "Favorited" if is_favorited else "Favorite"

                # This new handler ensures the image is in the gallery BEFORE favoriting
                def handle_outpainted_favorite():
                    # First, ensure the image exists in the main gallery
                    if not any(img['id'] == outpainted_data['id'] for img in st.session_state.images):
                        add_outpainted_to_gallery()
                    
                    # Now, call the universal favorite function you created earlier
                    toggle_and_save_favorite(outpainted_data['id'])

                st.button(
                    f"{star_icon} {fav_text}",
                    on_click=handle_outpainted_favorite, # Use our new handler
                    use_container_width=True,
                    key=f"fav_outpainted_{outpainted_data['id']}"
                )
                
    with st.expander("🖼️ Analyze Image to Create a Prompt", expanded=False):

        analysis_uploaded_image = st.file_uploader(
            "Upload an image to generate a descriptive prompt from it.",
            type=["png", "jpg", "jpeg", "webp"],
            key="analysis_uploader"
        )

        def apply_analyzed_prompt():
            st.session_state.main_prompt = st.session_state.analyzed_prompt_text
            st.success("Prompt copied to the main text area!")

        # This block now runs ONLY when a brand new image is uploaded.
        if analysis_uploaded_image and analysis_uploaded_image.file_id != st.session_state.current_analysis_file_id:
            st.session_state.current_analysis_file_id = analysis_uploaded_image.file_id
            st.session_state.analyzed_prompt_text = ""
            # --- FIX: Save the image object to session state ---
            st.session_state.analysis_image = Image.open(analysis_uploaded_image)

            with st.spinner("Letting the AI study your image..."):
                try:
                    prompt_for_analysis = [
                        "You are an expert prompt writer for AI image generators. Look at the provided image and write a single, detailed, plain-text prompt that could be used to generate a similar image. Do not include any analysis, explanations, headings, or markdown formatting. Only output the prompt itself.",
                        st.session_state.analysis_image # Use the image from session state
                    ]
                    analysis_response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt_for_analysis
                    )
                    st.session_state.analyzed_prompt_text = analysis_response.candidates[0].content.parts[0].text
                except Exception as e:
                    st.error(f"Could not analyze the image. Error: {e}")
                    # Clear all related state on error
                    st.session_state.analysis_image = None
                    st.session_state.current_analysis_file_id = None

        # --- FIX: Check for the image object in session state before displaying anything ---
        if st.session_state.analysis_image:
            # --- FIX: Display the image from session state, not the uploader variable ---
            st.image(st.session_state.analysis_image, caption="Image for Analysis", use_container_width=True)

            if st.session_state.analyzed_prompt_text:
                st.markdown("**📝 Generated Prompt:**")
                st.text_area("You can copy or use this prompt:", value=st.session_state.analyzed_prompt_text, height=150, key="analyzed_prompt_display")
                st.button("✍️ Use This Prompt", use_container_width=True, on_click=apply_analyzed_prompt)

            # --- FIX: The clear button now resets all related state variables ---
            if st.button("🗑️ Clear Analysis", use_container_width=True):
                st.session_state.analyzed_prompt_text = ""
                st.session_state.current_analysis_file_id = None
                st.session_state.analysis_image = None # Also clear the image object
                st.rerun()
        else:
             st.info("Please upload an image to begin analysis.")

    # --- END: FINAL ROBUST IMAGE-TO-PROMPT ---

    # --- END: FINAL POLISHED IMAGE-TO-PROMPT (REVISED PROMPT) ---

    # --- END: FINAL POLISHED IMAGE-TO-PROMPT ---

    # --- END: FINAL POLISHED IMAGE-TO-PROMPT ---

    # --- START: CHAT WITH YOUR IMAGE ---
    # --- START: CHAT WITH YOUR IMAGE (WITH CLEAR BUTTON) ---
    # --- START: CHAT WITH YOUR IMAGE (FINAL VERSION) ---
    with st.expander("💬 Chat with Your Image", expanded=False):

        chat_uploaded_image = st.file_uploader(
            "Upload an image to start a conversation about it.",
            type=["png", "jpg", "jpeg", "webp"],
            key="chat_uploader"
        )

        # Only reset the chat if a NEW image is uploaded
        if chat_uploaded_image and chat_uploaded_image.file_id != st.session_state.current_chat_file_id:
            st.session_state.current_chat_file_id = chat_uploaded_image.file_id
            st.session_state.chat_image = Image.open(chat_uploaded_image)
            st.session_state.image_chat_history = [] # Reset history for the new image
            st.info("New image loaded. You can now start chatting.")


        if st.session_state.chat_image:
            st.image(st.session_state.chat_image, caption="Image for Conversation", use_container_width=True)

            # --- Action Buttons: Clear and Download ---
            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button("🗑️ Clear Conversation", use_container_width=True):
                    st.session_state.image_chat_history = []
                    st.rerun()

            with action_col2:
                # The download button will only appear if there's a chat history
                if st.session_state.image_chat_history:
                    # Format the chat history into a downloadable text string
                    chat_log = ""
                    for message in st.session_state.image_chat_history:
                        role = "You" if message["role"] == "user" else "AI"
                        chat_log += f"{role}:\n{message['content']}\n\n"
                    
                    st.download_button(
                        label="💾 Download Chat",
                        data=chat_log.encode('utf-8'),
                        file_name=f"image_chat_{int(time.time())}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"download_chat_{st.session_state.current_chat_file_id}"
                    )

            # Display the chat history
            for message in st.session_state.image_chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input remains the same
            if question := st.chat_input("Ask a question about the image..."):
                st.session_state.image_chat_history.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)

                with st.spinner("AI is analyzing..."):
                    try:
                        chat_contents = [question, st.session_state.chat_image]

                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=chat_contents
                        )
                        
                        ai_response = response.candidates[0].content.parts[0].text
                        st.session_state.image_chat_history.append({"role": "assistant", "content": ai_response})
                        
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        else:
            st.info("Please upload an image to begin your chat.")
            
    # --- END: CHAT WITH YOUR IMAGE (FINAL VERSION) ---
            
    # --- END: CHAT WITH YOUR IMAGE (WITH CLEAR BUTTON) ---
            
    # --- END: CORRECTED CHAT WITH YOUR IMAGE ---

    # --- END: CHAT WITH YOUR IMAGE ---
    # --- END: IMAGE-TO-PROMPT (REVERSE IMAGE SEARCH) ---

    # --- START: COLOR PALETTE GENERATOR ---
    with st.expander("🎨 Color Palette Generator", expanded=False):
        st.info("Upload an image to extract its dominant color palette.")
        
        palette_image = st.file_uploader(
            "Upload your image for color extraction",
            type=["png", "jpg", "jpeg", "webp"],
            key="palette_uploader"
        )

        if palette_image:
            # Reset results if a new image is uploaded
            if 'palette_img_bytes' not in st.session_state or palette_image.getvalue() != st.session_state.get('palette_img_bytes'):
                st.session_state.palette_img_bytes = palette_image.getvalue()
                st.session_state.palette_result = None
                st.session_state.palette_image_dict = None

            original_pil_palette = Image.open(BytesIO(st.session_state.palette_img_bytes))
            st.image(original_pil_palette, caption="Image for Palette Extraction", use_container_width=True)

            num_colors = st.slider("Number of Colors to Extract", 2, 16, 5, key="palette_num_colors")

            if st.button("🎨 Extract Palette", use_container_width=True):
                with st.spinner("Analyzing colors..."):
                    try:
                        # Resize for performance
                        img_resized = original_pil_palette.resize((100, 100))
                        # Convert to numpy array
                        img_array = np.array(img_resized.convert("RGB"))
                        # Reshape to a list of pixels
                        pixels = img_array.reshape(-1, 3)
                        
                        # Use KMeans to find dominant colors
                        kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init='auto').fit(pixels)
                        dominant_colors = kmeans.cluster_centers_.astype(int)
                        
                        # Convert RGB to Hex
                        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dominant_colors]
                        
                        st.session_state.palette_result = hex_colors
                        # Create and save the palette image data to session state
                        swatch_size = 100
                        palette_img_obj = Image.new('RGB', (len(hex_colors) * swatch_size, swatch_size))
                        draw = ImageDraw.Draw(palette_img_obj)
                        for i, color in enumerate(hex_colors):
                            color_swatch = Image.new('RGB', (swatch_size, swatch_size), color)
                            palette_img_obj.paste(color_swatch, (i * swatch_size, 0))
                        
                        img_buffer = BytesIO()
                        palette_img_obj.save(img_buffer, format="PNG")
                        
                        st.session_state.palette_image_dict = {
                            "id": str(uuid.uuid4()),
                            "data": img_buffer.getvalue()
                        }
                    except Exception as e:
                        st.error(f"Color extraction failed: {e}")

        # Display the palette result if it exists
        # Display the palette result if it exists
        if 'palette_image_dict' in st.session_state and st.session_state.palette_image_dict:
            st.markdown("#### ✨ Extracted Palette")
            
            hex_colors = st.session_state.palette_result
            result_dict = st.session_state.palette_image_dict
            result_data = result_dict['data']
            image_id = result_dict['id']

            cols = st.columns(len(hex_colors))
            for i, hex_color in enumerate(hex_colors):
                with cols[i]:
                    st.markdown(f'<div style="background-color: {hex_color}; height: 80px; width: 100%; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);"></div>', unsafe_allow_html=True)
                    st.code(hex_color, language=None)
            
            st.markdown("---")
            st.markdown("##### 💾 Download Palette")
            
            dl_col1, dl_col2 = st.columns(2)

            with dl_col1:
                palette_json = json.dumps({"colors": hex_colors}, indent=2)
                st.download_button(
                    label="📄 Download JSON",
                    data=palette_json,
                    file_name=f"palette_info_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"download_palette_json_{image_id}"
                )

            with dl_col2:
                st.download_button(
                    label="🖼️ Download Image",
                    data=result_data,
                    file_name=f"palette_image_{int(time.time())}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"download_palette_image_{image_id}"
                )
            
            # Add to Gallery and Favorite buttons for the palette image
            b_col1, b_col2 = st.columns(2)
            
            def add_palette_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': result_data,
                        'original_prompt': "Color Palette Image",
                        'enhanced_prompt': "Image created with the Color Palette Generator utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Color Palette', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image of a color palette extracted from another image.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_palette_{image_id}"):
                    add_palette_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_palette():
                    add_palette_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_palette,
                    use_container_width=True,
                    key=f"fav_palette_{image_id}"
                )
            # --- END: ADDED DOWNLOAD OPTIONS ---
    # --- END: COLOR PALETTE GENERATOR ---

    # --- START: IMAGE COLORIZER ---
    with st.expander("🏞️ Image Colorizer", expanded=False):
        st.info("Bring black and white photos to life by adding realistic color.")
        
        colorizer_image = st.file_uploader(
            "Upload a black and white image to colorize",
            type=["png", "jpg", "jpeg", "webp"],
            key="colorizer_uploader"
        )

        if colorizer_image:
            # When a new image is uploaded, clear the previous result
            if 'colorizer_img_bytes' not in st.session_state or colorizer_image.getvalue() != st.session_state.get('colorizer_img_bytes'):
                st.session_state.colorizer_img_bytes = colorizer_image.getvalue()
                st.session_state.colorized_result_data = None

            original_pil_colorize = Image.open(BytesIO(st.session_state.colorizer_img_bytes))
            st.image(original_pil_colorize, caption=f"Original B&W Image ({original_pil_colorize.size[0]}x{original_pil_colorize.size[1]})")

            if st.button("🎨 Generate Colorized Image", use_container_width=True):
                with st.spinner("Breathing life and color into the image..."):
                    try:
                        # This prompt is crucial for telling the model to colorize
                        colorize_prompt = (
                            "You are an expert photo restoration artist specializing in colorization. "
                            "Colorize the provided black and white image. "
                            "The goal is to produce a realistic, vibrant, and historically/contextually appropriate result. "
                            "Pay close attention to skin tones, natural landscapes, and material textures. "
                            "Do not alter the original composition or content, only add color."
                        )

                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=[colorize_prompt, original_pil_colorize],
                            config=types.GenerateContentConfig(response_modalities=["text", "image"])
                        )
                        
                        st.session_state.colorized_result_dict = None
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                st.session_state.colorized_result_dict = {
                                    "id": str(uuid.uuid4()),
                                    "data": part.inline_data.data,
                                    "original_filename": colorizer_image.name
                                }
                                break

#                        if not st.session_state.colorized_result_data:
 #                           st.error("The model did not return a colorized image. Please try again.")

                    except Exception as e:
                        st.error(f"Colorization failed: {e}")

        # Display the colorized result if it exists
        # Display the colorized result if it exists
        if 'colorized_result_dict' in st.session_state and st.session_state.colorized_result_dict:
            st.markdown("---")
            st.markdown("#### ✨ Colorized Result")

            result_dict = st.session_state.colorized_result_dict
            colorized_data = result_dict['data']
            image_id = result_dict['id']
            original_filename = result_dict.get('original_filename', f"image_{int(time.time())}.png")

            result_img_colorized = Image.open(BytesIO(colorized_data))
            
            st.image(result_img_colorized, use_container_width=True, caption=f"Colorized Image ({result_img_colorized.size[0]}x{result_img_colorized.size[1]})")
            
            st.download_button(
                label="📥 Download Colorized Image",
                data=colorized_data,
                file_name=f"colorized_{original_filename}",
                mime="image/png",
                use_container_width=True,
                key=f"download_colorized_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_colorized_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': colorized_data,
                        'original_prompt': f"Colorized: {original_filename}",
                        'enhanced_prompt': "Image created with the Image Colorizer utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Colorizer', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Image Colorizer feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_colorized_{image_id}"):
                    add_colorized_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_colorized():
                    add_colorized_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_colorized,
                    use_container_width=True,
                    key=f"fav_colorized_{image_id}"
                )
    # --- END: IMAGE COLORIZER ---

    # --- START: ASCII ART GENERATOR ---
    with st.expander("📝 ASCII Art Generator", expanded=False):
        st.info("Convert any image into text-based ASCII art.")
        
        ascii_image_file = st.file_uploader(
            "Upload an image to convert to ASCII",
            type=["png", "jpg", "jpeg", "webp"],
            key="ascii_uploader"
        )

        if ascii_image_file:
            if 'ascii_img_bytes' not in st.session_state or ascii_image_file.getvalue() != st.session_state.get('ascii_img_bytes'):
                st.session_state.ascii_img_bytes = ascii_image_file.getvalue()
                st.session_state.ascii_art_result = None

            original_pil_ascii = Image.open(BytesIO(st.session_state.ascii_img_bytes))
            st.image(original_pil_ascii, caption="Image for ASCII Conversion", use_container_width=True)

            st.markdown("##### ⚙️ ASCII Settings")
            ascii_width = st.slider("Output Width (characters)", 50, 300, 100, key="ascii_width")
            ASCII_CHARS_OPTIONS = {
                "Detailed": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
                "Simple": "@%#*+=-:. ",
                "Blocks": "█▓▒░ "
            }
            char_option = st.selectbox("Character Set", list(ASCII_CHARS_OPTIONS.keys()), key="ascii_chars")
            invert_colors = st.checkbox("Light text on dark background", key="ascii_invert")

            if st.button("📝 Generate ASCII Art", use_container_width=True):
                with st.spinner("Converting pixels to text..."):
                    try:
                        ASCII_CHARS = ASCII_CHARS_OPTIONS[char_option]
                        if not invert_colors: # Default is dark text on light, so we reverse the dense-to-sparse list
                            ASCII_CHARS = ASCII_CHARS[::-1]
                        
                        width, height = original_pil_ascii.size
                        aspect_ratio = height / width
                        new_height = int(aspect_ratio * ascii_width * 0.55) # Correction factor for char aspect ratio
                        resized_image = original_pil_ascii.resize((ascii_width, new_height))
                        grayscale_image = resized_image.convert("L")
                        
                        pixels = list(grayscale_image.getdata())
                        ascii_str = "\n".join("".join(ASCII_CHARS[pixel * (len(ASCII_CHARS)-1) // 255] for pixel in pixels[i:i+ascii_width]) for i in range(0, len(pixels), ascii_width))
                        st.session_state.ascii_art_result = ascii_str
                    except Exception as e:
                        st.error(f"ASCII conversion failed: {e}")

        if 'ascii_art_result' in st.session_state and st.session_state.ascii_art_result:
            st.markdown("---")
            st.markdown("#### ✨ ASCII Art Result")
            ascii_result = st.session_state.ascii_art_result
            st.code(ascii_result, language=None)
            st.download_button(
                label="💾 Download as .txt file",
                data=ascii_result,
                file_name=f"ascii_art_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True
            )
    # --- END: ASCII ART GENERATOR ---

    # --- START: PENCIL SKETCH CONVERTER ---
    with st.expander("✏️ Pencil Sketch Converter", expanded=False):
        st.info("Convert a color photo into a beautiful, artistic pencil sketch.")
        
        sketch_image_file = st.file_uploader(
            "Upload an image to convert to a sketch",
            type=["png", "jpg", "jpeg", "webp"],
            key="sketch_uploader"
        )

        if sketch_image_file:
            if 'sketch_img_bytes' not in st.session_state or sketch_image_file.getvalue() != st.session_state.get('sketch_img_bytes'):
                st.session_state.sketch_img_bytes = sketch_image_file.getvalue()
                st.session_state.sketch_art_result = None

            original_pil_sketch = Image.open(BytesIO(st.session_state.sketch_img_bytes))
            st.image(original_pil_sketch, caption="Original Image for Sketching", use_container_width=True)

            st.markdown("##### ⚙️ Sketch Settings")
            blur_radius = st.slider("Blur Intensity (for line thickness)", 1, 25, 5, key="sketch_blur")

            if st.button("✏️ Generate Sketch", use_container_width=True):
                with st.spinner("Sketching your image..."):
                    try:
                        # 1. Convert to grayscale
                        grayscale_image = original_pil_sketch.convert("L")
                        
                        # 2. Invert the grayscale image
                        inverted_image = ImageOps.invert(grayscale_image)
                        
                        # 3. Apply Gaussian blur
                        blurred_image = inverted_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                        
                        # 4. Blend using Color Dodge
                        # Convert to numpy arrays for calculations
                        grayscale_np = np.array(grayscale_image, dtype=np.float32)
                        blurred_np = np.array(blurred_image, dtype=np.float32)
                        
                        # To avoid division by zero, add a small epsilon
                        epsilon = 1e-6
                        sketch_np = (grayscale_np * 255.0) / (255.0 - blurred_np + epsilon)
                        
                        # Clip values to be in the 0-255 range
                        sketch_np = np.clip(sketch_np, 0, 255)
                        
                        # Convert back to an image
                        sketch_image = Image.fromarray(sketch_np.astype('uint8'))
                        
                        # Save result to session state
                        output_buffer = BytesIO()
                        sketch_image.save(output_buffer, format="PNG")
                        st.session_state.sketch_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}

                    except Exception as e:
                        st.error(f"Sketch conversion failed: {e}")

        if 'sketch_art_dict' in st.session_state and st.session_state.sketch_art_dict:
            st.markdown("---")
            st.markdown("#### ✨ Sketch Result")

            result_dict = st.session_state.sketch_art_dict
            result_data = result_dict['data']
            image_id = result_dict['id']
            
            st.image(result_data, use_container_width=True, caption="Your generated sketch")
            
            st.download_button(
                label="💾 Download as .png file",
                data=result_data,
                file_name=f"sketch_art_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True,
                key=f"download_sketch_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_sketch_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': result_data,
                        'original_prompt': "Image from Pencil Sketch Converter",
                        'enhanced_prompt': "Image created with the Pencil Sketch utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Pencil Sketch', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Pencil Sketch feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_sketch_{image_id}"):
                    add_sketch_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_sketch():
                    add_sketch_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_sketch,
                    use_container_width=True,
                    key=f"fav_sketch_{image_id}"
                )
    # --- END: PENCIL SKETCH CONVERTER ---

    # --- START: GLITCH ART GENERATOR ---
    with st.expander("👾 Glitch Art Generator", expanded=False):
        st.info("Add a cool, retro, digital glitch effect to your images.")
        
        glitch_image_file = st.file_uploader(
            "Upload an image to apply a glitch effect",
            type=["png", "jpg", "jpeg", "webp"],
            key="glitch_uploader"
        )

        if glitch_image_file:
            if 'glitch_img_bytes' not in st.session_state or glitch_image_file.getvalue() != st.session_state.get('glitch_img_bytes'):
                st.session_state.glitch_img_bytes = glitch_image_file.getvalue()
                st.session_state.glitch_art_result = None

            original_pil_glitch = Image.open(BytesIO(st.session_state.glitch_img_bytes))
            st.image(original_pil_glitch, caption="Original Image for Glitching", use_container_width=True)

            st.markdown("##### ⚙️ Glitch Settings")
            glitch_amount = st.slider("Glitch Intensity", 1, 10, 3, key="glitch_amount", help="How many times to apply a random glitch.")
            glitch_seed = st.number_input("Glitch Seed (for reproducibility)", value=42, key="glitch_seed")
            
            if st.button("👾 Generate Glitch Art", use_container_width=True):
                with st.spinner("Corrupting data streams..."):
                    try:
                        random.seed(glitch_seed)
                        np.random.seed(glitch_seed)
                        img_np = np.array(original_pil_glitch.convert("RGB"))
                        h, w, c = img_np.shape
                        for _ in range(glitch_amount):
                            glitch_type = random.choice(['shift', 'color_block', 'channel_swap'])
                            if glitch_type == 'shift':
                                line_to_shift, shift_amount = random.randint(0, h - 1), random.randint(-w // 4, w // 4)
                                img_np[line_to_shift, :, :] = np.roll(img_np[line_to_shift, :, :], shift_amount, axis=0)
                            elif glitch_type == 'color_block':
                                x1, y1 = random.randint(0, w-20), random.randint(0, h-20)
                                x2, y2 = x1 + random.randint(10, 50), y1 + random.randint(10, 50)
                                img_np[y1:y2, x1:x2, :] = np.random.randint(0, 255, size=3)
                            elif glitch_type == 'channel_swap':
                                start_row, end_row = random.randint(0, h - 20), random.randint(5, 20)
                                channels = random.sample([0, 1, 2], 2)
                                img_np[start_row:start_row+end_row, :, channels[0]], img_np[start_row:start_row+end_row, :, channels[1]] = \
                                    img_np[start_row:start_row+end_row, :, channels[1]].copy(), img_np[start_row:start_row+end_row, :, channels[0]].copy()
                        glitch_image = Image.fromarray(img_np)
                        output_buffer = BytesIO()
                        glitch_image.save(output_buffer, format="PNG")
                        st.session_state.glitch_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                    except Exception as e:
                        st.error(f"Glitch effect failed: {e}")

        if 'glitch_art_dict' in st.session_state and st.session_state.glitch_art_dict:
            st.markdown("---")
            st.markdown("#### ✨ Glitch Art Result")
            
            result_dict = st.session_state.glitch_art_dict
            result_data = result_dict['data']
            image_id = result_dict['id']

            st.image(result_data, use_container_width=True, caption="Your glitched masterpiece")
            
            st.download_button(
                label="💾 Download as .png file",
                data=result_data,
                file_name=f"glitch_art_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True,
                key=f"download_glitch_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_glitch_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': result_data,
                        'original_prompt': "Image from Glitch Art Generator",
                        'enhanced_prompt': "Image created with the Glitch Art utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Glitch Art', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Glitch Art feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_glitch_{image_id}"):
                    add_glitch_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_glitch():
                    add_glitch_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_glitch,
                    use_container_width=True,
                    key=f"fav_glitch_{image_id}"
                )
    # --- END: GLITCH ART GENERATOR ---

    # --- START: HALFTONE PRINT EFFECT ---
    with st.expander("📰 Halftone Print Effect", expanded=False):
        st.info("Recreate the classic dotted print effect seen in newspapers and comics. Color mode works best with larger dot scales.")

        halftone_image_file = st.file_uploader(
            "Upload an image to apply the halftone effect",
            type=["png", "jpg", "jpeg", "webp"],
            key="halftone_uploader"
        )

        if halftone_image_file:
            if 'halftone_img_bytes' not in st.session_state or halftone_image_file.getvalue() != st.session_state.get('halftone_img_bytes'):
                st.session_state.halftone_img_bytes = halftone_image_file.getvalue()
                st.session_state.halftone_art_result = None

            original_pil_halftone = Image.open(BytesIO(st.session_state.halftone_img_bytes))
            st.image(original_pil_halftone, caption="Original Image for Halftone Effect", use_container_width=True)

            st.markdown("##### ⚙️ Halftone Settings")

            cols_ht = st.columns(2)
            with cols_ht[0]:
                halftone_scale = st.slider("Dot Scale (Grid Size)", 4, 32, 10, key="halftone_scale", help="The size of the grid cells. Smaller values mean more, smaller dots.")
            with cols_ht[1]:
                halftone_mode = st.selectbox("Mode", ["Color", "Monochrome"], key="halftone_mode")

            if st.button("📰 Generate Halftone Effect", use_container_width=True):
                with st.spinner("Arranging dots into your image... This can take a moment for large images."):
                    try:
                        source_img = original_pil_halftone.convert("RGB")
                        output_img = Image.new("RGB", source_img.size, (255, 255, 255))
                        draw = ImageDraw.Draw(output_img)
                        width, height = source_img.size
                        source_pixels = source_img.load()

                        for y in range(0, height, halftone_scale):
                            for x in range(0, width, halftone_scale):
                                r_total, g_total, b_total, num_pixels = 0, 0, 0, 0
                                for i in range(x, min(x + halftone_scale, width)):
                                    for j in range(y, min(y + halftone_scale, height)):
                                        r, g, b = source_pixels[i, j]
                                        r_total += r; g_total += g; b_total += b
                                        num_pixels += 1
                                
                                if num_pixels == 0: continue

                                avg_r, avg_g, avg_b = r_total / num_pixels, g_total / num_pixels, b_total / num_pixels
                                center_x, center_y = x + halftone_scale / 2, y + halftone_scale / 2

                                if halftone_mode == "Monochrome":
                                    brightness = (avg_r + avg_g + avg_b) / 3
                                    dot_radius_factor = 1.0 - (brightness / 255.0)
                                    max_dot_radius = halftone_scale / 2 * 1.4
                                    dot_radius = dot_radius_factor * max_dot_radius
                                    box = [center_x - dot_radius, center_y - dot_radius, center_x + dot_radius, center_y + dot_radius]
                                    draw.ellipse(box, fill=(0, 0, 0))
                                else: # Color mode (CMY approximation)
                                    c, m, y_c = 1.0 - (avg_r / 255.0), 1.0 - (avg_g / 255.0), 1.0 - (avg_b / 255.0)
                                    max_dot_radius, offset = halftone_scale / 2 * 1.4, halftone_scale / 3
                                    
                                    c_radius = c * max_dot_radius
                                    draw.ellipse([center_x - c_radius - offset, center_y - c_radius - offset, center_x + c_radius - offset, center_y + c_radius - offset], fill=(0, 255, 255))
                                    m_radius = m * max_dot_radius
                                    draw.ellipse([center_x - m_radius + offset, center_y - m_radius, center_x + m_radius + offset, center_y + m_radius], fill=(255, 0, 255))
                                    y_radius = y_c * max_dot_radius
                                    draw.ellipse([center_x - y_radius, center_y - y_radius + offset, center_x + y_radius, center_y + y_radius + offset], fill=(255, 255, 0))

                        output_buffer = BytesIO()
                        output_img.save(output_buffer, format="PNG")
                        st.session_state.halftone_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                    except Exception as e:
                        st.error(f"Halftone effect failed: {e}")

        if 'halftone_art_dict' in st.session_state and st.session_state.halftone_art_dict:
            st.markdown("---")
            st.markdown("#### ✨ Halftone Result")

            result_dict = st.session_state.halftone_art_dict
            result_data = result_dict['data']
            image_id = result_dict['id']

            st.image(result_data, use_container_width=True, caption="Your generated halftone print")
            
            st.download_button(
                label="💾 Download as .png file", 
                data=result_data, 
                file_name=f"halftone_art_{int(time.time())}.png", 
                mime="image/png", 
                use_container_width=True,
                key=f"download_halftone_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_halftone_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': result_data,
                        'original_prompt': "Image from Halftone Print Effect",
                        'enhanced_prompt': "Image created with the Halftone Print utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Halftone', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Halftone Print feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_halftone_{image_id}"):
                    add_halftone_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_halftone():
                    add_halftone_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_halftone,
                    use_container_width=True,
                    key=f"fav_halftone_{image_id}"
                )
    # --- END: HALFTONE PRINT EFFECT ---

    # --- START: BACKGROUND REMOVAL TOOL ---
    with st.expander("✂️ Background Remover", expanded=False):
        st.info("Automatically remove the background from an image, leaving only the main subject.")
        
        bg_remover_image_file = st.file_uploader(
            "Upload an image to remove its background",
            type=["png", "jpg", "jpeg", "webp"],
            key="bg_remover_uploader"
        )

        if bg_remover_image_file:
            # When a new image is uploaded, clear the previous result
            if 'bg_remover_img_bytes' not in st.session_state or bg_remover_image_file.getvalue() != st.session_state.get('bg_remover_img_bytes'):
                st.session_state.bg_remover_img_bytes = bg_remover_image_file.getvalue()
                st.session_state.bg_remover_result_dict = None

            original_pil_bg = Image.open(BytesIO(st.session_state.bg_remover_img_bytes))
            st.image(original_pil_bg, caption="Original Image", use_container_width=True)

            if st.button("✂️ Remove Background", use_container_width=True):
                with st.spinner("Isolating the subject from its background..."):
                    try:
                        # This prompt is crucial for telling the model to remove the background
                        bg_removal_prompt = (
                            "You are an expert image editor. Your task is to accurately remove the background from the provided image. "
                            "The output must be the main subject with a fully transparent background. "
                            "Do not alter the subject itself. The final image should be a PNG with an alpha channel."
                        )

                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=[bg_removal_prompt, original_pil_bg],
                            config=types.GenerateContentConfig(response_modalities=["text", "image"])
                        )
                        
                        st.session_state.bg_remover_result_dict = None
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                st.session_state.bg_remover_result_dict = {
                                    "id": str(uuid.uuid4()),
                                    "data": part.inline_data.data,
                                    "original_filename": bg_remover_image_file.name
                                }
                                break

                        if not st.session_state.bg_remover_result_dict:
                            st.error("The model did not return an image. Please try again.")

                    except Exception as e:
                        st.error(f"Background removal failed: {e}")

        # Display the result if it exists
        if 'bg_remover_result_dict' in st.session_state and st.session_state.bg_remover_result_dict:
            st.markdown("---")
            st.markdown("#### ✨ Background Removed Result")

            result_dict = st.session_state.bg_remover_result_dict
            result_data = result_dict['data']
            image_id = result_dict['id']
            original_filename = result_dict.get('original_filename', f"image_{int(time.time())}.png")
            
            st.image(result_data, use_container_width=True, caption="Image with background removed")
            
            st.download_button(
                label="📥 Download Image (PNG)",
                data=result_data,
                file_name=f"no_bg_{original_filename}",
                mime="image/png",
                use_container_width=True,
                key=f"download_bg_removed_{image_id}"
            )

            # Add to Gallery and Favorite buttons
            b_col1, b_col2 = st.columns(2)
            
            def add_bg_removed_to_gallery():
                if not any(img['id'] == image_id for img in st.session_state.images):
                    gallery_metadata = {
                        'id': image_id, 'image_data': result_data,
                        'original_prompt': f"Background removed from: {original_filename}",
                        'enhanced_prompt': "Image created with the Background Remover utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'style_used': 'Background Remover', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Background Remover feature.',
                        'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    st.session_state.images.append(gallery_metadata)
                    save_image_to_db(gallery_metadata)
                    st.toast("✅ Added to gallery!")

            with b_col1:
                is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_bg_removed_{image_id}"):
                    add_bg_removed_to_gallery()
                    st.rerun()

            with b_col2:
                is_favorited = image_id in st.session_state.favorites
                star_icon = "★" if is_favorited else "☆"
                def handle_favorite_bg_removed():
                    add_bg_removed_to_gallery()
                    toggle_and_save_favorite(image_id)
                st.button(
                    f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                    on_click=handle_favorite_bg_removed,
                    use_container_width=True,
                    key=f"fav_bg_removed_{image_id}"
                )
    # --- END: BACKGROUND REMOVAL TOOL ---


    # --- START: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # This container is now outside the 'if' condition, so it appears on startup.
    # --- START: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # This container is now outside the 'if' condition, so it appears on startup.
    st.markdown("### 🪄 Miscellaneous Toolkit")

    misc_tool_options = [
        "--- Select a Tool ---",
        "🎲 Surprise Me! (Random Prompt)",
        "🎨 Image Inverter",
        "🎞️ Sepia Tone Filter",
        "⚫ Grayscale Converter",
        "↔️ Image Flipper",
        "✒️ Edge Detection",
        "🖼️ Posterize Effect",
        "☀️ Brightness & Contrast",
        "✨ Sharpen Filter",
        "💧 Blur Filter",
        "🌞 Solarize Effect",
        "🗿 Emboss Filter",
        "🗺️ Contour Filter",
        "🔲 Add Border",
        "🔄 Image Rotator",
        "🚦 Channel Splitter",
        "🔳 Threshold Filter",
        "🎨 Duotone Effect",
        "👾 Pixelate Effect"
    ]
    
    # Add 10 more tools to reach 30 total options
    misc_tool_options.extend([
        "🌈 Saturation Control",
        "🔳 Auto Contrast",
        "📊 Equalize Histogram",
        "💧 Gaussian Blur",
        "🔪 Unsharp Mask",
        "🔤 Add Watermark",
        "🌃 Vignette Effect",
        "🎨 Color Quantization",
        "💡 Gamma Correction",
        "🖌️ Median Filter (Smudge)"
    ])
    
    # Add 10 more tools to reach 40 total options
    misc_tool_options.extend([
        "✂️ Image Cropper",
        "⚖️ Color Balance",
        "🖌️ Oil Painting Effect",
        "✒️ Charcoal Sketch Effect",
        "🌡️ Color Temperature",
        "🎲 Add Noise",
        "✒️ Find Edges (Advanced)",
        "📈 Color Curves (Simple)",
        "↔️ Image Resizer",
        "💧 Create Reflection"
    ])
    
    # Add the final 10 tools to reach 50 total options
    misc_tool_options.extend([
        "💥 Comic Book Effect",
        "🪩 Chromatic Aberration",
        "🤏 Tilt-Shift (Miniature)",
        "📐 Blueprint Effect",
        "🕶️ Anaglyph 3D Effect",
        "🎨 Pop Art Effect",
        "☀️ Light Leak Effect",
        "🌙 Night Vision Effect",
        "📺 Scanlines (CRT) Effect",
        "🧊 Frosted Glass Effect"
    ])
    selected_misc_tool = st.selectbox("Select a tool from the toolkit:", misc_tool_options, key="misc_tool_selector")

    if selected_misc_tool == "🎲 Surprise Me! (Random Prompt)":
        with st.container(border=True):
            st.markdown("##### ✨ Feeling Lucky?")
            def generate_random_prompt():
                subjects = [
                    "A majestic dragon soaring over a volcanic landscape", "An ancient tree spirit with glowing eyes",
                    "A celestial fox with nine tails, leaping through stars", "A forgotten library in the clouds",
                    "A knight in ethereal, glowing armor", "A city carved into a giant crystal",
                    "A futuristic city skyline at sunset", "A robot gardener tending to glowing alien plants",
                    "An alien marketplace on a distant planet", "A lone astronaut discovering an ancient alien artifact",
                    "A Roman legion marching through a dense forest", "A samurai warrior meditating under a cherry blossom tree",
                    "A hidden waterfall oasis in a lush jungle", "A majestic lion with a crown of stars",
                    "A clock melting over a branch, in the style of Dali", "A staircase that spirals into the clouds",
                    "An old watchmaker in his workshop, surrounded by timepieces", "A street artist painting a mural on a brick wall"
                ]
                details = [
                    "in the style of a classical oil painting", "as a vibrant watercolor illustration",
                    "in the style of Hayao Miyazaki", "in the style of a detailed charcoal sketch",
                    "with an impressionist art style, visible brush strokes", "in a surrealist style, like Salvador Dalí",
                    "with a pop art aesthetic, like Andy Warhol", "as a vintage Japanese ukiyo-e woodblock print",
                    "with dramatic, cinematic lighting", "with an ethereal, otherworldly glow",
                    "in vibrant, rich, saturated colors", "with a soft, dreamy, and gentle focus",
                    "rendered in Unreal Engine 5, hyperrealistic", "as a hyper-detailed, 8K resolution photograph",
                    "with a glossy, reflective finish", "with a rough, textured, matte finish"
                ]
                full_prompt = f"{random.choice(subjects)}, {random.choice(details)}"
                st.session_state.main_prompt = full_prompt

            st.button(
                "🎲 Generate Random Prompt",
                on_click=generate_random_prompt,
                use_container_width=True,
                help="Generate a random, creative prompt to get you started."
            )

    elif selected_misc_tool == "🎨 Image Inverter":
        with st.expander("🎨 Image Inverter", expanded=True):
            st.info("Invert the colors of any image.")
            
            inverter_image_file = st.file_uploader(
                "Upload an image to invert its colors",
                type=["png", "jpg", "jpeg", "webp"],
                key="inverter_uploader"
            )

            if inverter_image_file:
                if 'inverter_img_bytes' not in st.session_state or inverter_image_file.getvalue() != st.session_state.get('inverter_img_bytes'):
                    st.session_state.inverter_img_bytes = inverter_image_file.getvalue()
                    st.session_state.inverter_art_dict = None

                original_pil_inverter = Image.open(BytesIO(st.session_state.inverter_img_bytes))
                st.image(original_pil_inverter, caption="Original Image", use_container_width=True)

                if st.button("🎨 Invert Colors", use_container_width=True):
                    with st.spinner("Flipping bits and bytes..."):
                        try:
                            rgb_image = original_pil_inverter.convert("RGB")
                            inverted_image = ImageOps.invert(rgb_image)
                            
                            output_buffer = BytesIO()
                            inverted_image.save(output_buffer, format="PNG")
                            st.session_state.inverter_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Inversion failed: {e}")

            if 'inverter_art_dict' in st.session_state and st.session_state.inverter_art_dict:
                st.markdown("---")
                st.markdown("#### ✨ Inverted Result")

                result_dict = st.session_state.inverter_art_dict
                result_data = result_dict['data']
                image_id = result_dict['id']
                
                st.image(result_data, use_container_width=True, caption="Your inverted image")
                
                st.download_button(
                    label="💾 Download as .png file",
                    data=result_data,
                    file_name=f"inverted_art_{int(time.time())}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"download_inverted_{image_id}"
                )

                b_col1, b_col2 = st.columns(2)
                
                def add_inverted_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        gallery_metadata = {
                            'id': image_id, 'image_data': result_data,
                            'original_prompt': "Image from Image Inverter",
                            'enhanced_prompt': "Image created with the Image Inverter utility.",
                            'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'style_used': 'Image Inverter', 'color_mood': 'N/A', 'lighting': 'N/A',
                            'description': 'Image created using the Image Inverter feature.',
                            'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                        }
                        st.session_state.images.append(gallery_metadata)
                        save_image_to_db(gallery_metadata)
                        st.toast("✅ Added to gallery!")

                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_inverted_{image_id}"):
                        add_inverted_to_gallery()
                        st.rerun()

                with b_col2:
                    is_favorited = image_id in st.session_state.favorites
                    star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_inverted():
                        add_inverted_to_gallery()
                        toggle_and_save_favorite(image_id)
                    st.button(
                        f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}",
                        on_click=handle_favorite_inverted,
                        use_container_width=True,
                        key=f"fav_inverted_{image_id}"
                    )
    
    elif selected_misc_tool == "🎞️ Sepia Tone Filter":
        with st.expander("🎞️ Sepia Tone Filter", expanded=True):
            st.info("Apply a classic, brownish sepia tone to your image for a vintage look.")
            
            sepia_image_file = st.file_uploader("Upload an image to apply sepia tone", type=["png", "jpg", "jpeg", "webp"], key="sepia_uploader")

            if sepia_image_file:
                if 'sepia_img_bytes' not in st.session_state or sepia_image_file.getvalue() != st.session_state.get('sepia_img_bytes'):
                    st.session_state.sepia_img_bytes = sepia_image_file.getvalue()
                    st.session_state.sepia_art_dict = None

                original_pil_sepia = Image.open(BytesIO(st.session_state.sepia_img_bytes))
                st.image(original_pil_sepia, caption="Original Image", use_container_width=True)

                if st.button("🎞️ Apply Sepia Filter", use_container_width=True):
                    with st.spinner("Applying vintage filter..."):
                        try:
                            img = original_pil_sepia.convert("RGB")
                            img_np = np.array(img, dtype=np.float32)
                            sepia_matrix = np.array([[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]])
                            sepia_img_np = img_np.dot(sepia_matrix.T)
                            sepia_img_np = np.clip(sepia_img_np, 0, 255)
                            sepia_image = Image.fromarray(sepia_img_np.astype('uint8'))
                            
                            output_buffer = BytesIO()
                            sepia_image.save(output_buffer, format="PNG")
                            st.session_state.sepia_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Sepia conversion failed: {e}")

            if 'sepia_art_dict' in st.session_state and st.session_state.sepia_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Sepia Result")
                result_dict = st.session_state.sepia_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your sepia image")
                st.download_button("💾 Download as .png", result_data, f"sepia_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_sepia_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_sepia_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Sepia Filter", 'enhanced_prompt': "Image created with the Sepia Filter utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Sepia Filter', 'color_mood': 'Vintage', 'lighting': 'N/A', 'description': 'Image created using the Sepia Filter feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_sepia_{image_id}"):
                        add_sepia_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_sepia(): add_sepia_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_sepia, use_container_width=True, key=f"fav_sepia_{image_id}")

    elif selected_misc_tool == "⚫ Grayscale Converter":
        with st.expander("⚫ Grayscale Converter", expanded=True):
            st.info("Convert any color image to black and white.")
            
            grayscale_image_file = st.file_uploader("Upload an image to convert to grayscale", type=["png", "jpg", "jpeg", "webp"], key="grayscale_uploader")

            if grayscale_image_file:
                if 'grayscale_img_bytes' not in st.session_state or grayscale_image_file.getvalue() != st.session_state.get('grayscale_img_bytes'):
                    st.session_state.grayscale_img_bytes = grayscale_image_file.getvalue()
                    st.session_state.grayscale_art_dict = None

                original_pil_grayscale = Image.open(BytesIO(st.session_state.grayscale_img_bytes))
                st.image(original_pil_grayscale, caption="Original Image", use_container_width=True)

                if st.button("⚫ Convert to Grayscale", use_container_width=True):
                    with st.spinner("Removing colors..."):
                        try:
                            grayscale_image = original_pil_grayscale.convert("L")
                            output_buffer = BytesIO()
                            grayscale_image.save(output_buffer, format="PNG")
                            st.session_state.grayscale_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Grayscale conversion failed: {e}")

            if 'grayscale_art_dict' in st.session_state and st.session_state.grayscale_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Grayscale Result")
                result_dict = st.session_state.grayscale_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your grayscale image")
                st.download_button("💾 Download as .png", result_data, f"grayscale_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_grayscale_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_grayscale_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Grayscale Converter", 'enhanced_prompt': "Image created with the Grayscale Converter utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Grayscale', 'color_mood': 'Monochrome', 'lighting': 'N/A', 'description': 'Image created using the Grayscale Converter feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_grayscale_{image_id}"):
                        add_grayscale_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_grayscale(): add_grayscale_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_grayscale, use_container_width=True, key=f"fav_grayscale_{image_id}")

    elif selected_misc_tool == "↔️ Image Flipper":
        with st.expander("↔️ Image Flipper", expanded=True):
            st.info("Flip an image horizontally (mirror) or vertically.")
            
            flipper_image_file = st.file_uploader("Upload an image to flip", type=["png", "jpg", "jpeg", "webp"], key="flipper_uploader")

            if flipper_image_file:
                if 'flipper_img_bytes' not in st.session_state or flipper_image_file.getvalue() != st.session_state.get('flipper_img_bytes'):
                    st.session_state.flipper_img_bytes = flipper_image_file.getvalue()
                    st.session_state.flipper_art_dict = None

                original_pil_flipper = Image.open(BytesIO(st.session_state.flipper_img_bytes))
                st.image(original_pil_flipper, caption="Original Image", use_container_width=True)

                flip_mode = st.radio("Flip Direction", ["Horizontal (Mirror)", "Vertical"], key="flip_mode_selector", horizontal=True)

                if st.button("↔️ Flip Image", use_container_width=True):
                    with st.spinner("Flipping image..."):
                        try:
                            if flip_mode == "Horizontal (Mirror)":
                                flipped_image = ImageOps.mirror(original_pil_flipper)
                            else: # Vertical
                                flipped_image = ImageOps.flip(original_pil_flipper)
                            
                            output_buffer = BytesIO()
                            flipped_image.save(output_buffer, format="PNG")
                            st.session_state.flipper_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Image flip failed: {e}")

            if 'flipper_art_dict' in st.session_state and st.session_state.flipper_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Flipped Result")
                result_dict = st.session_state.flipper_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your flipped image")
                st.download_button("💾 Download as .png", result_data, f"flipped_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_flipper_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_flipper_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Image Flipper", 'enhanced_prompt': "Image created with the Image Flipper utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Image Flipper', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Image Flipper feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_flipper_{image_id}"):
                        add_flipper_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_flipper(): add_flipper_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_flipper, use_container_width=True, key=f"fav_flipper_{image_id}")

    elif selected_misc_tool == "✒️ Edge Detection":
        with st.expander("✒️ Edge Detection", expanded=True):
            st.info("Create a stylized image that highlights the edges and outlines.")
            
            edge_image_file = st.file_uploader("Upload an image to detect its edges", type=["png", "jpg", "jpeg", "webp"], key="edge_uploader")

            if edge_image_file:
                if 'edge_img_bytes' not in st.session_state or edge_image_file.getvalue() != st.session_state.get('edge_img_bytes'):
                    st.session_state.edge_img_bytes = edge_image_file.getvalue()
                    st.session_state.edge_art_dict = None

                original_pil_edge = Image.open(BytesIO(st.session_state.edge_img_bytes))
                st.image(original_pil_edge, caption="Original Image", use_container_width=True)

                if st.button("✒️ Find Edges", use_container_width=True):
                    with st.spinner("Scanning for edges..."):
                        try:
                            edge_image = original_pil_edge.convert("L").filter(ImageFilter.FIND_EDGES)
                            output_buffer = BytesIO()
                            edge_image.save(output_buffer, format="PNG")
                            st.session_state.edge_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Edge detection failed: {e}")

            if 'edge_art_dict' in st.session_state and st.session_state.edge_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Edge Detection Result")
                result_dict = st.session_state.edge_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your edge-detected image")
                st.download_button("💾 Download as .png", result_data, f"edge_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_edge_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_edge_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Edge Detection", 'enhanced_prompt': "Image created with the Edge Detection utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Edge Detection', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Edge Detection feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_edge_{image_id}"):
                        add_edge_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_edge(): add_edge_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_edge, use_container_width=True, key=f"fav_edge_{image_id}")

    elif selected_misc_tool == "🖼️ Posterize Effect":
        with st.expander("🖼️ Posterize Effect", expanded=True):
            st.info("Reduce the number of colors in the image to create a 'poster' look.")
            
            posterize_image_file = st.file_uploader("Upload an image to posterize", type=["png", "jpg", "jpeg", "webp"], key="posterize_uploader")

            if posterize_image_file:
                if 'posterize_img_bytes' not in st.session_state or posterize_image_file.getvalue() != st.session_state.get('posterize_img_bytes'):
                    st.session_state.posterize_img_bytes = posterize_image_file.getvalue()
                    st.session_state.posterize_art_dict = None

                original_pil_posterize = Image.open(BytesIO(st.session_state.posterize_img_bytes))
                st.image(original_pil_posterize, caption="Original Image", use_container_width=True)

                bits = st.slider("Color Depth (Bits per channel)", 1, 8, 4, key="posterize_bits", help="Fewer bits mean fewer colors and a stronger effect.")

                if st.button("🖼️ Apply Posterize Effect", use_container_width=True):
                    with st.spinner("Reducing color palette..."):
                        try:
                            posterized_image = ImageOps.posterize(original_pil_posterize.convert("RGB"), bits)
                            output_buffer = BytesIO()
                            posterized_image.save(output_buffer, format="PNG")
                            st.session_state.posterize_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Posterize effect failed: {e}")

            if 'posterize_art_dict' in st.session_state and st.session_state.posterize_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Posterized Result")
                result_dict = st.session_state.posterize_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your posterized image")
                st.download_button("💾 Download as .png", result_data, f"poster_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_posterize_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_posterize_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Posterize Effect", 'enhanced_prompt': "Image created with the Posterize Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Posterize', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Posterize Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_posterize_{image_id}"):
                        add_posterize_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_posterize(): add_posterize_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_posterize, use_container_width=True, key=f"fav_posterize_{image_id}")

    elif selected_misc_tool == "☀️ Brightness & Contrast":
        with st.expander("☀️ Brightness & Contrast", expanded=True):
            st.info("Adjust the brightness and contrast of your image.")
            
            bc_image_file = st.file_uploader("Upload an image to adjust", type=["png", "jpg", "jpeg", "webp"], key="bc_uploader")

            if bc_image_file:
                if 'bc_img_bytes' not in st.session_state or bc_image_file.getvalue() != st.session_state.get('bc_img_bytes'):
                    st.session_state.bc_img_bytes = bc_image_file.getvalue()
                    st.session_state.bc_art_dict = None

                original_pil_bc = Image.open(BytesIO(st.session_state.bc_img_bytes))
                st.image(original_pil_bc, caption="Original Image", use_container_width=True)

                brightness = st.slider("Brightness", 0.5, 1.5, 1.0, 0.05, key="brightness_slider")
                contrast = st.slider("Contrast", 0.5, 1.5, 1.0, 0.05, key="contrast_slider")

                if st.button("☀️ Apply Adjustments", use_container_width=True):
                    with st.spinner("Adjusting levels..."):
                        try:
                            enhancer_b = ImageEnhance.Brightness(original_pil_bc)
                            img_bright = enhancer_b.enhance(brightness)
                            enhancer_c = ImageEnhance.Contrast(img_bright)
                            img_final = enhancer_c.enhance(contrast)
                            
                            output_buffer = BytesIO()
                            img_final.save(output_buffer, format="PNG")
                            st.session_state.bc_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Adjustment failed: {e}")

            if 'bc_art_dict' in st.session_state and st.session_state.bc_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Adjusted Result")
                result_dict = st.session_state.bc_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your adjusted image")
                st.download_button("💾 Download as .png", result_data, f"adjusted_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_bc_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_bc_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Brightness/Contrast", 'enhanced_prompt': "Image created with the Brightness/Contrast utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Brightness/Contrast', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Brightness/Contrast feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_bc_{image_id}"):
                        add_bc_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_bc(): add_bc_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_bc, use_container_width=True, key=f"fav_bc_{image_id}")

    elif selected_misc_tool in ["✨ Sharpen Filter", "💧 Blur Filter", "🌞 Solarize Effect", "🗿 Emboss Filter", "🗺️ Contour Filter"]:
        tool_configs = {
            "✨ Sharpen Filter": {"name": "Sharpen", "filter": ImageFilter.SHARPEN, "spinner_text": "Sharpening edges..."},
            "💧 Blur Filter": {"name": "Blur", "filter": ImageFilter.BLUR, "spinner_text": "Applying blur..."},
            "🌞 Solarize Effect": {"name": "Solarize", "filter": None, "spinner_text": "Solarizing..."}, # Special case
            "🗿 Emboss Filter": {"name": "Emboss", "filter": ImageFilter.EMBOSS, "spinner_text": "Applying emboss filter..."},
            "🗺️ Contour Filter": {"name": "Contour", "filter": ImageFilter.CONTOUR, "spinner_text": "Finding contours..."}
        }
        config = tool_configs[selected_misc_tool]
        tool_name_lower = config['name'].lower()

        with st.expander(selected_misc_tool, expanded=True):
            st.info(f"Apply a {tool_name_lower} effect to your image.")
            
            image_file = st.file_uploader(f"Upload an image to apply {tool_name_lower} effect", type=["png", "jpg", "jpeg", "webp"], key=f"{tool_name_lower}_uploader")

            if image_file:
                if f'{tool_name_lower}_img_bytes' not in st.session_state or image_file.getvalue() != st.session_state.get(f'{tool_name_lower}_img_bytes'):
                    st.session_state[f'{tool_name_lower}_img_bytes'] = image_file.getvalue()
                    st.session_state[f'{tool_name_lower}_art_dict'] = None

                original_pil = Image.open(BytesIO(st.session_state[f'{tool_name_lower}_img_bytes']))
                st.image(original_pil, caption="Original Image", use_container_width=True)

                solarize_threshold = None
                if config['name'] == "Solarize":
                    solarize_threshold = st.slider("Solarize Threshold", 0, 255, 128)

                if st.button(f"{selected_misc_tool.split(' ')[0]} Apply {config['name']} Filter", use_container_width=True):
                    with st.spinner(config['spinner_text']):
                        try:
                            if config['name'] == "Solarize":
                                processed_image = ImageOps.solarize(original_pil.convert("RGB"), threshold=solarize_threshold)
                            else:
                                processed_image = original_pil.filter(config['filter'])
                            
                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state[f'{tool_name_lower}_art_dict'] = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"{config['name']} effect failed: {e}")

            if f'{tool_name_lower}_art_dict' in st.session_state and st.session_state[f'{tool_name_lower}_art_dict']:
                st.markdown(f"---"); st.markdown(f"#### ✨ {config['name']} Result")
                result_dict = st.session_state[f'{tool_name_lower}_art_dict']
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Your {tool_name_lower} image")
                st.download_button("💾 Download as .png", result_data, f"{tool_name_lower}_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_{tool_name_lower}_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': f"Image from {config['name']} Filter", 'enhanced_prompt': f"Image created with the {config['name']} Filter utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': f"{config['name']} Filter", 'color_mood': 'N/A', 'lighting': 'N/A', 'description': f"Image created using the {config['name']} Filter feature.", 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_{tool_name_lower}_{image_id}"):
                        add_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite(): add_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite, use_container_width=True, key=f"fav_{tool_name_lower}_{image_id}")

    elif selected_misc_tool == "🔲 Add Border":
        with st.expander("🔲 Add Border", expanded=True):
            st.info("Add a simple, colored border around your image.")
            
            border_image_file = st.file_uploader("Upload an image to add a border", type=["png", "jpg", "jpeg", "webp"], key="border_uploader")

            if border_image_file:
                if 'border_img_bytes' not in st.session_state or border_image_file.getvalue() != st.session_state.get('border_img_bytes'):
                    st.session_state.border_img_bytes = border_image_file.getvalue()
                    st.session_state.border_art_dict = None

                original_pil_border = Image.open(BytesIO(st.session_state.border_img_bytes))
                st.image(original_pil_border, caption="Original Image", use_container_width=True)

                border_size = st.slider("Border Size (pixels)", 1, 100, 10, key="border_size")
                border_color = st.color_picker("Border Color", "#FFFFFF", key="border_color")

                if st.button("🔲 Add Border", use_container_width=True):
                    with st.spinner("Framing your image..."):
                        try:
                            bordered_image = ImageOps.expand(original_pil_border, border=border_size, fill=border_color)
                            output_buffer = BytesIO()
                            bordered_image.save(output_buffer, format="PNG")
                            st.session_state.border_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Adding border failed: {e}")

            if 'border_art_dict' in st.session_state and st.session_state.border_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Bordered Result")
                result_dict = st.session_state.border_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your bordered image")
                st.download_button("💾 Download as .png", result_data, f"bordered_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_border_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_border_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Add Border", 'enhanced_prompt': "Image created with the Add Border utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Add Border', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Add Border feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_border_{image_id}"):
                        add_border_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_border(): add_border_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_border, use_container_width=True, key=f"fav_border_{image_id}")

    elif selected_misc_tool == "🔄 Image Rotator":
        with st.expander("🔄 Image Rotator", expanded=True):
            st.info("Rotate your image by a fixed angle.")
            
            rotator_image_file = st.file_uploader("Upload an image to rotate", type=["png", "jpg", "jpeg", "webp"], key="rotator_uploader")

            if rotator_image_file:
                if 'rotator_img_bytes' not in st.session_state or rotator_image_file.getvalue() != st.session_state.get('rotator_img_bytes'):
                    st.session_state.rotator_img_bytes = rotator_image_file.getvalue()
                    st.session_state.rotator_art_dict = None

                original_pil_rotator = Image.open(BytesIO(st.session_state.rotator_img_bytes))
                st.image(original_pil_rotator, caption="Original Image", use_container_width=True)

                angle = st.selectbox("Rotation Angle", [90, 180, 270], index=0, format_func=lambda x: f"{x}° Clockwise")

                if st.button("🔄 Rotate Image", use_container_width=True):
                    with st.spinner("Rotating image..."):
                        try:
                            # PIL rotates counter-clockwise, so we use negative for clockwise
                            rotated_image = original_pil_rotator.rotate(-angle, expand=True)
                            output_buffer = BytesIO()
                            rotated_image.save(output_buffer, format="PNG")
                            st.session_state.rotator_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Rotation failed: {e}")

            if 'rotator_art_dict' in st.session_state and st.session_state.rotator_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Rotated Result")
                result_dict = st.session_state.rotator_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your rotated image")
                st.download_button("💾 Download as .png", result_data, f"rotated_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_rotator_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_rotator_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Image Rotator", 'enhanced_prompt': "Image created with the Image Rotator utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Image Rotator', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Image Rotator feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_rotator_{image_id}"):
                        add_rotator_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_rotator(): add_rotator_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_rotator, use_container_width=True, key=f"fav_rotator_{image_id}")

    elif selected_misc_tool == "🚦 Channel Splitter":
        with st.expander("🚦 Channel Splitter", expanded=True):
            st.info("Isolate and view the Red, Green, or Blue channels of an image.")
            
            channel_image_file = st.file_uploader("Upload an image to split channels", type=["png", "jpg", "jpeg", "webp"], key="channel_uploader")

            if channel_image_file:
                if 'channel_img_bytes' not in st.session_state or channel_image_file.getvalue() != st.session_state.get('channel_img_bytes'):
                    st.session_state.channel_img_bytes = channel_image_file.getvalue()
                    st.session_state.channel_art_dict = None

                original_pil_channel = Image.open(BytesIO(st.session_state.channel_img_bytes)).convert("RGB")
                st.image(original_pil_channel, caption="Original Image", use_container_width=True)

                channel_to_show = st.radio("Channel to Display", ["Red", "Green", "Blue"], key="channel_selector", horizontal=True)

                if st.button("🚦 Split Channels", use_container_width=True):
                    with st.spinner(f"Isolating {channel_to_show} channel..."):
                        try:
                            r, g, b = original_pil_channel.split()
                            channel_map = {"Red": r, "Green": g, "Blue": b}
                            
                            # Create a black image to paste the channel into
                            zero_channel = Image.new('L', original_pil_channel.size, 0)
                            
                            if channel_to_show == "Red":
                                processed_image = Image.merge("RGB", (channel_map["Red"], zero_channel, zero_channel))
                            elif channel_to_show == "Green":
                                processed_image = Image.merge("RGB", (zero_channel, channel_map["Green"], zero_channel))
                            else: # Blue
                                processed_image = Image.merge("RGB", (zero_channel, zero_channel, channel_map["Blue"]))

                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state.channel_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Channel splitting failed: {e}")

            if 'channel_art_dict' in st.session_state and st.session_state.channel_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Channel Result")
                result_dict = st.session_state.channel_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Isolated {channel_to_show} Channel")
                st.download_button("💾 Download as .png", result_data, f"channel_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_channel_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_channel_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Channel Splitter", 'enhanced_prompt': "Image created with the Channel Splitter utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Channel Splitter', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Channel Splitter feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_channel_{image_id}"):
                        add_channel_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_channel(): add_channel_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_channel, use_container_width=True, key=f"fav_channel_{image_id}")

    elif selected_misc_tool == "🔳 Threshold Filter":
        with st.expander("🔳 Threshold Filter", expanded=True):
            st.info("Convert an image to pure black and white based on a luminance threshold.")
            
            threshold_image_file = st.file_uploader("Upload an image to apply threshold", type=["png", "jpg", "jpeg", "webp"], key="threshold_uploader")

            if threshold_image_file:
                if 'threshold_img_bytes' not in st.session_state or threshold_image_file.getvalue() != st.session_state.get('threshold_img_bytes'):
                    st.session_state.threshold_img_bytes = threshold_image_file.getvalue()
                    st.session_state.threshold_art_dict = None

                original_pil_threshold = Image.open(BytesIO(st.session_state.threshold_img_bytes))
                st.image(original_pil_threshold, caption="Original Image", use_container_width=True)

                threshold_value = st.slider("Luminance Threshold", 0, 255, 128, key="threshold_value")

                if st.button("🔳 Apply Threshold", use_container_width=True):
                    with st.spinner("Applying threshold..."):
                        try:
                            grayscale_image = original_pil_threshold.convert("L")
                            threshold_image = grayscale_image.point(lambda p: 255 if p > threshold_value else 0, '1')
                            
                            output_buffer = BytesIO()
                            threshold_image.save(output_buffer, format="PNG")
                            st.session_state.threshold_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Threshold failed: {e}")

            if 'threshold_art_dict' in st.session_state and st.session_state.threshold_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Threshold Result")
                result_dict = st.session_state.threshold_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your threshold image")
                st.download_button("💾 Download as .png", result_data, f"threshold_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_threshold_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_threshold_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Threshold Filter", 'enhanced_prompt': "Image created with the Threshold Filter utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Threshold Filter', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Threshold Filter feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_threshold_{image_id}"):
                        add_threshold_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_threshold(): add_threshold_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_threshold, use_container_width=True, key=f"fav_threshold_{image_id}")

    elif selected_misc_tool == "🎨 Duotone Effect":
        with st.expander("🎨 Duotone Effect", expanded=True):
            st.info("Recolor an image using two specified colors for the dark and light tones.")
            
            duotone_image_file = st.file_uploader("Upload an image for duotone effect", type=["png", "jpg", "jpeg", "webp"], key="duotone_uploader")

            if duotone_image_file:
                if 'duotone_img_bytes' not in st.session_state or duotone_image_file.getvalue() != st.session_state.get('duotone_img_bytes'):
                    st.session_state.duotone_img_bytes = duotone_image_file.getvalue()
                    st.session_state.duotone_art_dict = None

                original_pil_duotone = Image.open(BytesIO(st.session_state.duotone_img_bytes))
                st.image(original_pil_duotone, caption="Original Image", use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    dark_color = st.color_picker("Dark Color", "#000080", key="duotone_dark")
                with col2:
                    light_color = st.color_picker("Light Color", "#FFFF00", key="duotone_light")

                if st.button("🎨 Apply Duotone", use_container_width=True):
                    with st.spinner("Recoloring image..."):
                        try:
                            grayscale_image = original_pil_duotone.convert("L")
                            duotone_image = ImageOps.colorize(grayscale_image, black=dark_color, white=light_color)
                            
                            output_buffer = BytesIO()
                            duotone_image.save(output_buffer, format="PNG")
                            st.session_state.duotone_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Duotone effect failed: {e}")

            if 'duotone_art_dict' in st.session_state and st.session_state.duotone_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Duotone Result")
                result_dict = st.session_state.duotone_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your duotone image")
                st.download_button("💾 Download as .png", result_data, f"duotone_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_duotone_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_duotone_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Duotone Effect", 'enhanced_prompt': "Image created with the Duotone Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Duotone Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Duotone Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_duotone_{image_id}"):
                        add_duotone_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_duotone(): add_duotone_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_duotone, use_container_width=True, key=f"fav_duotone_{image_id}")

    elif selected_misc_tool == "👾 Pixelate Effect":
        with st.expander("👾 Pixelate Effect", expanded=True):
            st.info("Create a retro, blocky, pixelated version of your image.")
            
            pixelate_image_file = st.file_uploader("Upload an image to pixelate", type=["png", "jpg", "jpeg", "webp"], key="pixelate_uploader")

            if pixelate_image_file:
                if 'pixelate_img_bytes' not in st.session_state or pixelate_image_file.getvalue() != st.session_state.get('pixelate_img_bytes'):
                    st.session_state.pixelate_img_bytes = pixelate_image_file.getvalue()
                    st.session_state.pixelate_art_dict = None

                original_pil_pixelate = Image.open(BytesIO(st.session_state.pixelate_img_bytes))
                st.image(original_pil_pixelate, caption="Original Image", use_container_width=True)

                pixel_size = st.slider("Pixel Size", 2, 32, 8, key="pixelate_size", help="Larger values create a more blocky, abstract effect.")

                if st.button("👾 Pixelate Image", use_container_width=True):
                    with st.spinner("Downsampling image..."):
                        try:
                            img = original_pil_pixelate.copy()
                            # Resize down to pixelated size
                            small_img = img.resize(
                                (img.size[0] // pixel_size, img.size[1] // pixel_size),
                                resample=Image.Resampling.BILINEAR
                            )
                            # Resize back up to original size
                            pixelated_image = small_img.resize(
                                img.size,
                                resample=Image.Resampling.NEAREST
                            )
                            
                            output_buffer = BytesIO()
                            pixelated_image.save(output_buffer, format="PNG")
                            st.session_state.pixelate_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Pixelate effect failed: {e}")

            if 'pixelate_art_dict' in st.session_state and st.session_state.pixelate_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Pixelated Result")
                result_dict = st.session_state.pixelate_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your pixelated image")
                st.download_button("💾 Download as .png", result_data, f"pixelate_art_{int(time.time())}.png", "image/png", use_container_width=True, key=f"download_pixelate_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_pixelate_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Pixelate Effect", 'enhanced_prompt': "Image created with the Pixelate Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Pixelate Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Pixelate Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", use_container_width=True, disabled=is_in_gallery, key=f"gallery_pixelate_{image_id}"):
                        add_pixelate_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_pixelate(): add_pixelate_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_pixelate, use_container_width=True, key=f"fav_pixelate_{image_id}")

    elif selected_misc_tool == "🌈 Saturation Control":
        with st.expander("🌈 Saturation Control", expanded=True):
            st.info("Adjust the color saturation of your image. 0 is grayscale, 1 is original, >1 is more vibrant.")
            
            saturation_image_file = st.file_uploader("Upload an image to adjust saturation", type=["png", "jpg", "jpeg", "webp"], key="saturation_uploader")

            if saturation_image_file:
                if 'saturation_img_bytes' not in st.session_state or saturation_image_file.getvalue() != st.session_state.get('saturation_img_bytes'):
                    st.session_state.saturation_img_bytes = saturation_image_file.getvalue()
                    st.session_state.saturation_art_dict = None

                original_pil_saturation = Image.open(BytesIO(st.session_state.saturation_img_bytes))
                st.image(original_pil_saturation, caption="Original Image", use_container_width=True)

                saturation_factor = st.slider("Saturation Factor", 0.0, 3.0, 1.0, 0.1, key="saturation_factor")

                if st.button("🌈 Apply Saturation", width='stretch'):
                    with st.spinner("Adjusting saturation..."):
                        try:
                            enhancer = ImageEnhance.Color(original_pil_saturation)
                            saturated_image = enhancer.enhance(saturation_factor)
                            
                            output_buffer = BytesIO()
                            saturated_image.save(output_buffer, format="PNG")
                            st.session_state.saturation_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Saturation adjustment failed: {e}")

            if 'saturation_art_dict' in st.session_state and st.session_state.saturation_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Saturation Result")
                result_dict = st.session_state.saturation_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your saturated image")
                st.download_button("💾 Download as .png", result_data, f"saturated_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_saturation_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_saturation_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Saturation Control", 'enhanced_prompt': "Image created with the Saturation Control utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Saturation Control', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Saturation Control feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_saturation_{image_id}"):
                        add_saturation_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_saturation(): add_saturation_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_saturation, width='stretch', key=f"fav_saturation_{image_id}")

    elif selected_misc_tool in ["🔳 Auto Contrast", "📊 Equalize Histogram"]:
        tool_configs = {
            "🔳 Auto Contrast": {"name": "Auto Contrast", "op": ImageOps.autocontrast, "spinner_text": "Applying auto contrast..."},
            "📊 Equalize Histogram": {"name": "Equalize", "op": ImageOps.equalize, "spinner_text": "Equalizing histogram..."}
        }
        config = tool_configs[selected_misc_tool]
        tool_name_lower = config['name'].lower().replace(" ", "_")

        with st.expander(selected_misc_tool, expanded=True):
            st.info(f"Automatically enhance contrast using the {config['name']} method.")
            
            image_file = st.file_uploader(f"Upload an image to apply {config['name']}", type=["png", "jpg", "jpeg", "webp"], key=f"{tool_name_lower}_uploader")

            if image_file:
                if f'{tool_name_lower}_img_bytes' not in st.session_state or image_file.getvalue() != st.session_state.get(f'{tool_name_lower}_img_bytes'):
                    st.session_state[f'{tool_name_lower}_img_bytes'] = image_file.getvalue()
                    st.session_state[f'{tool_name_lower}_art_dict'] = None

                original_pil = Image.open(BytesIO(st.session_state[f'{tool_name_lower}_img_bytes']))
                st.image(original_pil, caption="Original Image", use_container_width=True)

                if st.button(f"{selected_misc_tool.split(' ')[0]} Apply {config['name']}", width='stretch'):
                    with st.spinner(config['spinner_text']):
                        try:
                            processed_image = config['op'](original_pil.convert("RGB"))
                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state[f'{tool_name_lower}_art_dict'] = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"{config['name']} failed: {e}")

            if f'{tool_name_lower}_art_dict' in st.session_state and st.session_state[f'{tool_name_lower}_art_dict']:
                st.markdown(f"---"); st.markdown(f"#### ✨ {config['name']} Result")
                result_dict = st.session_state[f'{tool_name_lower}_art_dict']
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Your {tool_name_lower} image")
                st.download_button("💾 Download as .png", result_data, f"{tool_name_lower}_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_{tool_name_lower}_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': f"Image from {config['name']}", 'enhanced_prompt': f"Image created with the {config['name']} utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': f"{config['name']}", 'color_mood': 'N/A', 'lighting': 'N/A', 'description': f"Image created using the {config['name']} feature.", 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_{tool_name_lower}_{image_id}"):
                        add_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite(): add_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite, width='stretch', key=f"fav_{tool_name_lower}_{image_id}")

    elif selected_misc_tool in ["💧 Gaussian Blur", "🔪 Unsharp Mask", "🖌️ Median Filter (Smudge)"]:
        tool_configs = {
            "💧 Gaussian Blur": {"name": "Gaussian Blur", "spinner_text": "Applying Gaussian blur..."},
            "🔪 Unsharp Mask": {"name": "Unsharp Mask", "spinner_text": "Applying unsharp mask..."},
            "🖌️ Median Filter (Smudge)": {"name": "Median Filter", "spinner_text": "Applying median filter..."}
        }
        config = tool_configs[selected_misc_tool]
        tool_name_lower = config['name'].lower().replace(" ", "_")

        with st.expander(selected_misc_tool, expanded=True):
            st.info(f"Apply the {config['name']} filter to your image.")
            
            image_file = st.file_uploader(f"Upload an image for {config['name']}", type=["png", "jpg", "jpeg", "webp"], key=f"{tool_name_lower}_uploader")

            if image_file:
                if f'{tool_name_lower}_img_bytes' not in st.session_state or image_file.getvalue() != st.session_state.get(f'{tool_name_lower}_img_bytes'):
                    st.session_state[f'{tool_name_lower}_img_bytes'] = image_file.getvalue()
                    st.session_state[f'{tool_name_lower}_art_dict'] = None

                original_pil = Image.open(BytesIO(st.session_state[f'{tool_name_lower}_img_bytes']))
                st.image(original_pil, caption="Original Image", use_container_width=True)

                radius, percent, threshold, size = 2, 150, 3, 3 # Defaults
                if config['name'] == "Gaussian Blur":
                    radius = st.slider("Blur Radius", 0, 50, 2, key="gblur_radius")
                elif config['name'] == "Unsharp Mask":
                    radius = st.slider("Radius", 0, 50, 2, key="unsharp_radius")
                    percent = st.slider("Percent", 0, 300, 150, key="unsharp_percent")
                    threshold = st.slider("Threshold", 0, 255, 3, key="unsharp_threshold")
                elif config['name'] == "Median Filter":
                    size = st.select_slider("Filter Size", options=[3, 5, 7, 9], value=3, key="median_size", help="Must be an odd number.")

                if st.button(f"{selected_misc_tool.split(' ')[0]} Apply Filter", width='stretch'):
                    with st.spinner(config['spinner_text']):
                        try:
                            if config['name'] == "Gaussian Blur":
                                processed_image = original_pil.filter(ImageFilter.GaussianBlur(radius=radius))
                            elif config['name'] == "Unsharp Mask":
                                processed_image = original_pil.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
                            elif config['name'] == "Median Filter":
                                processed_image = original_pil.filter(ImageFilter.MedianFilter(size=size))

                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state[f'{tool_name_lower}_art_dict'] = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Filter application failed: {e}")

            if f'{tool_name_lower}_art_dict' in st.session_state and st.session_state[f'{tool_name_lower}_art_dict']:
                st.markdown(f"---"); st.markdown(f"#### ✨ {config['name']} Result")
                result_dict = st.session_state[f'{tool_name_lower}_art_dict']
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Your {tool_name_lower} image")
                st.download_button("💾 Download as .png", result_data, f"{tool_name_lower}_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_{tool_name_lower}_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': f"Image from {config['name']}", 'enhanced_prompt': f"Image created with the {config['name']} utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': f"{config['name']}", 'color_mood': 'N/A', 'lighting': 'N/A', 'description': f"Image created using the {config['name']} feature.", 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_{tool_name_lower}_{image_id}"):
                        add_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite(): add_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite, width='stretch', key=f"fav_{tool_name_lower}_{image_id}")

    elif selected_misc_tool == "🔤 Add Watermark":
        with st.expander("🔤 Add Watermark", expanded=True):
            st.info("Add a text watermark to your image.")
            
            watermark_image_file = st.file_uploader("Upload an image to watermark", type=["png", "jpg", "jpeg", "webp"], key="watermark_uploader")

            if watermark_image_file:
                if 'watermark_img_bytes' not in st.session_state or watermark_image_file.getvalue() != st.session_state.get('watermark_img_bytes'):
                    st.session_state.watermark_img_bytes = watermark_image_file.getvalue()
                    st.session_state.watermark_art_dict = None

                original_pil_watermark = Image.open(BytesIO(st.session_state.watermark_img_bytes)).convert("RGBA")
                st.image(original_pil_watermark, caption="Original Image", use_container_width=True)

                c1, c2 = st.columns(2)
                text = c1.text_input("Watermark Text", "© DreamCanvas")
                opacity = c2.slider("Opacity", 0, 255, 128)
                c3, c4 = st.columns(2)
                position = c3.selectbox("Position", ["Bottom Right", "Bottom Left", "Top Left", "Top Right", "Center"])
                text_color = c4.color_picker("Text Color", "#FFFFFF")

                if st.button("🔤 Add Watermark", width='stretch'):
                    with st.spinner("Adding watermark..."):
                        try:
                            txt_img = Image.new("RGBA", original_pil_watermark.size, (255, 255, 255, 0))
                            draw = ImageDraw.Draw(txt_img)
                            font_size = int(original_pil_watermark.width / 20)
                            try:
                                font = ImageFont.truetype("arial.ttf", font_size)
                            except IOError:
                                font = ImageFont.load_default()

                            r, g, b = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                            
                            bbox = draw.textbbox((0,0), text, font=font)
                            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                            margin = 10
                            pos_map = {
                                "Bottom Right": (original_pil_watermark.width - text_w - margin, original_pil_watermark.height - text_h - margin),
                                "Bottom Left": (margin, original_pil_watermark.height - text_h - margin),
                                "Top Left": (margin, margin),
                                "Top Right": (original_pil_watermark.width - text_w - margin, margin),
                                "Center": ((original_pil_watermark.width - text_w) / 2, (original_pil_watermark.height - text_h) / 2)
                            }
                            draw.text(pos_map[position], text, font=font, fill=(r, g, b, opacity))
                            watermarked_image = Image.alpha_composite(original_pil_watermark, txt_img)

                            output_buffer = BytesIO()
                            watermarked_image.convert("RGB").save(output_buffer, format="PNG")
                            st.session_state.watermark_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Watermark failed: {e}")

            if 'watermark_art_dict' in st.session_state and st.session_state.watermark_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Watermarked Result")
                result_dict = st.session_state.watermark_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your watermarked image")
                st.download_button("💾 Download as .png", result_data, f"watermarked_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_watermark_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_watermark_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Add Watermark", 'enhanced_prompt': "Image created with the Add Watermark utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Add Watermark', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Add Watermark feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_watermark_{image_id}"):
                        add_watermark_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_watermark(): add_watermark_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_watermark, width='stretch', key=f"fav_watermark_{image_id}")

    elif selected_misc_tool == "🌃 Vignette Effect":
        with st.expander("🌃 Vignette Effect", expanded=True):
            st.info("Add a dark, circular border to focus attention on the center of the image.")
            
            vignette_image_file = st.file_uploader("Upload an image for a vignette effect", type=["png", "jpg", "jpeg", "webp"], key="vignette_uploader")

            if vignette_image_file:
                if 'vignette_img_bytes' not in st.session_state or vignette_image_file.getvalue() != st.session_state.get('vignette_img_bytes'):
                    st.session_state.vignette_img_bytes = vignette_image_file.getvalue()
                    st.session_state.vignette_art_dict = None

                original_pil_vignette = Image.open(BytesIO(st.session_state.vignette_img_bytes)).convert("RGB")
                st.image(original_pil_vignette, caption="Original Image", use_container_width=True)

                strength = st.slider("Vignette Strength", 0.1, 1.0, 0.5, 0.1, key="vignette_strength")

                if st.button("🌃 Apply Vignette", width='stretch'):
                    with st.spinner("Adding vignette..."):
                        try:
                            w, h = original_pil_vignette.size
                            gradient = Image.new('L', (w, h), 0)
                            draw = ImageDraw.Draw(gradient)
                            
                            for i in range(w):
                                for j in range(h):
                                    dist_x = (i - w / 2) ** 2
                                    dist_y = (j - h / 2) ** 2
                                    dist = (dist_x + dist_y) ** 0.5
                                    max_dist = ((w/2)**2 + (h/2)**2)**0.5
                                    val = int(255 * (dist / max_dist) ** strength)
                                    gradient.putpixel((i, j), val)

                            alpha = gradient.point(lambda p: 255 - p)
                            black_img = Image.new('RGB', (w, h), (0, 0, 0))
                            vignette_image = Image.composite(original_pil_vignette, black_img, alpha)

                            output_buffer = BytesIO()
                            vignette_image.save(output_buffer, format="PNG")
                            st.session_state.vignette_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Vignette effect failed: {e}")

            if 'vignette_art_dict' in st.session_state and st.session_state.vignette_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Vignette Result")
                result_dict = st.session_state.vignette_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your vignetted image")
                st.download_button("💾 Download as .png", result_data, f"vignette_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_vignette_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_vignette_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Vignette Effect", 'enhanced_prompt': "Image created with the Vignette Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Vignette Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Vignette Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_vignette_{image_id}"):
                        add_vignette_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_vignette(): add_vignette_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_vignette, width='stretch', key=f"fav_vignette_{image_id}")

    elif selected_misc_tool == "🎨 Color Quantization":
        with st.expander("🎨 Color Quantization", expanded=True):
            st.info("Simplify the image by reducing it to a limited number of colors, creating a stylized, poster-like effect.")
            
            quant_image_file = st.file_uploader("Upload an image to quantize", type=["png", "jpg", "jpeg", "webp"], key="quant_uploader")

            if quant_image_file:
                if 'quant_img_bytes' not in st.session_state or quant_image_file.getvalue() != st.session_state.get('quant_img_bytes'):
                    st.session_state.quant_img_bytes = quant_image_file.getvalue()
                    st.session_state.quant_art_dict = None

                original_pil_quant = Image.open(BytesIO(st.session_state.quant_img_bytes))
                st.image(original_pil_quant, caption="Original Image", use_container_width=True)

                num_colors = st.slider("Number of Colors", 2, 256, 16, key="quant_colors")

                if st.button("🎨 Apply Quantization", width='stretch'):
                    with st.spinner("Simplifying colors..."):
                        try:
                            # Quantize the image to a specific number of colors
                            quantized_image = original_pil_quant.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
                            # Convert back to RGB so it can be saved as PNG/JPG and displayed correctly
                            quantized_image = quantized_image.convert("RGB")

                            output_buffer = BytesIO()
                            quantized_image.save(output_buffer, format="PNG")
                            st.session_state.quant_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Color quantization failed: {e}")

            if 'quant_art_dict' in st.session_state and st.session_state.quant_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Quantized Result")
                result_dict = st.session_state.quant_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your quantized image")
                st.download_button("💾 Download as .png", result_data, f"quantized_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_quant_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_quant_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Color Quantization", 'enhanced_prompt': "Image created with the Color Quantization utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Color Quantization', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Color Quantization feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_quant_{image_id}"):
                        add_quant_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_quant(): add_quant_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_quant, width='stretch', key=f"fav_quant_{image_id}")

    elif selected_misc_tool == "💡 Gamma Correction":
        with st.expander("💡 Gamma Correction", expanded=True):
            st.info("Adjust the gamma to lighten or darken the mid-tones of the image.")
            
            gamma_image_file = st.file_uploader("Upload an image for gamma correction", type=["png", "jpg", "jpeg", "webp"], key="gamma_uploader")

            if gamma_image_file:
                if 'gamma_img_bytes' not in st.session_state or gamma_image_file.getvalue() != st.session_state.get('gamma_img_bytes'):
                    st.session_state.gamma_img_bytes = gamma_image_file.getvalue()
                    st.session_state.gamma_art_dict = None

                original_pil_gamma = Image.open(BytesIO(st.session_state.gamma_img_bytes))
                st.image(original_pil_gamma, caption="Original Image", use_container_width=True)

                gamma_value = st.slider("Gamma Value", 0.1, 5.0, 1.0, 0.1, key="gamma_value", help=">1 will lighten, <1 will darken.")

                if st.button("💡 Apply Gamma", width='stretch'):
                    with st.spinner("Correcting gamma..."):
                        try:
                            inv_gamma = 1.0 / gamma_value
                            table = [((i / 255.0) ** inv_gamma) * 255 for i in range(256)]
                            gamma_image = original_pil_gamma.convert("L").point(table)
                            if original_pil_gamma.mode == 'RGB':
                                r, g, b = original_pil_gamma.split()
                                r = r.point(table)
                                g = g.point(table)
                                b = b.point(table)
                                gamma_image = Image.merge('RGB', (r, g, b))
                            else:
                                gamma_image = original_pil_gamma.point(table)

                            output_buffer = BytesIO()
                            gamma_image.save(output_buffer, format="PNG")
                            st.session_state.gamma_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Gamma correction failed: {e}")

            if 'gamma_art_dict' in st.session_state and st.session_state.gamma_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Gamma Corrected Result")
                result_dict = st.session_state.gamma_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your gamma corrected image")
                st.download_button("💾 Download as .png", result_data, f"gamma_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_gamma_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_gamma_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Gamma Correction", 'enhanced_prompt': "Image created with the Gamma Correction utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Gamma Correction', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Gamma Correction feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_gamma_{image_id}"):
                        add_gamma_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_gamma(): add_gamma_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_gamma, width='stretch', key=f"fav_gamma_{image_id}")

    elif selected_misc_tool == "✂️ Image Cropper":
        with st.expander("✂️ Image Cropper", expanded=True):
            st.info("Crop an image by specifying the coordinates of the bounding box.")
            
            cropper_image_file = st.file_uploader("Upload an image to crop", type=["png", "jpg", "jpeg", "webp"], key="cropper_uploader")

            if cropper_image_file:
                if 'cropper_img_bytes' not in st.session_state or cropper_image_file.getvalue() != st.session_state.get('cropper_img_bytes'):
                    st.session_state.cropper_img_bytes = cropper_image_file.getvalue()
                    st.session_state.cropper_art_dict = None

                original_pil_cropper = Image.open(BytesIO(st.session_state.cropper_img_bytes))
                st.image(original_pil_cropper, caption=f"Original Image ({original_pil_cropper.width}x{original_pil_cropper.height})", use_container_width=True)

                c1, c2 = st.columns(2)
                left = c1.number_input("Left (X1)", 0, original_pil_cropper.width - 1, 0)
                top = c2.number_input("Top (Y1)", 0, original_pil_cropper.height - 1, 0)
                right = c1.number_input("Right (X2)", left + 1, original_pil_cropper.width, original_pil_cropper.width)
                bottom = c2.number_input("Bottom (Y2)", top + 1, original_pil_cropper.height, original_pil_cropper.height)

                if st.button("✂️ Crop Image", width='stretch'):
                    with st.spinner("Cropping..."):
                        try:
                            cropped_image = original_pil_cropper.crop((left, top, right, bottom))
                            output_buffer = BytesIO()
                            cropped_image.save(output_buffer, format="PNG")
                            st.session_state.cropper_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Cropping failed: {e}")

            if 'cropper_art_dict' in st.session_state and st.session_state.cropper_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Cropped Result")
                result_dict = st.session_state.cropper_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your cropped image")
                st.download_button("💾 Download as .png", result_data, f"cropped_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_cropper_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_cropper_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Image Cropper", 'enhanced_prompt': "Image created with the Image Cropper utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Image Cropper', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Image Cropper feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_cropper_{image_id}"):
                        add_cropper_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_cropper(): add_cropper_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_cropper, width='stretch', key=f"fav_cropper_{image_id}")

    elif selected_misc_tool == "⚖️ Color Balance":
        with st.expander("⚖️ Color Balance", expanded=True):
            st.info("Adjust the balance of Red, Green, and Blue channels.")
            
            balance_image_file = st.file_uploader("Upload an image to balance colors", type=["png", "jpg", "jpeg", "webp"], key="balance_uploader")

            if balance_image_file:
                if 'balance_img_bytes' not in st.session_state or balance_image_file.getvalue() != st.session_state.get('balance_img_bytes'):
                    st.session_state.balance_img_bytes = balance_image_file.getvalue()
                    st.session_state.balance_art_dict = None

                original_pil_balance = Image.open(BytesIO(st.session_state.balance_img_bytes)).convert("RGB")
                st.image(original_pil_balance, caption="Original Image", use_container_width=True)

                r_factor = st.slider("Red Balance", 0.0, 2.0, 1.0, 0.05, key="red_balance")
                g_factor = st.slider("Green Balance", 0.0, 2.0, 1.0, 0.05, key="green_balance")
                b_factor = st.slider("Blue Balance", 0.0, 2.0, 1.0, 0.05, key="blue_balance")

                if st.button("⚖️ Apply Color Balance", width='stretch'):
                    with st.spinner("Balancing colors..."):
                        try:
                            r, g, b = original_pil_balance.split()
                            r = r.point(lambda i: i * r_factor)
                            g = g.point(lambda i: i * g_factor)
                            b = b.point(lambda i: i * b_factor)
                            balanced_image = Image.merge("RGB", (r, g, b))

                            output_buffer = BytesIO()
                            balanced_image.save(output_buffer, format="PNG")
                            st.session_state.balance_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Color balance failed: {e}")

            if 'balance_art_dict' in st.session_state and st.session_state.balance_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Color Balanced Result")
                result_dict = st.session_state.balance_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your color balanced image")
                st.download_button("💾 Download as .png", result_data, f"balanced_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_balance_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_balance_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Color Balance", 'enhanced_prompt': "Image created with the Color Balance utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Color Balance', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Color Balance feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_balance_{image_id}"):
                        add_balance_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_balance(): add_balance_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_balance, width='stretch', key=f"fav_balance_{image_id}")

    elif selected_misc_tool in ["🖌️ Oil Painting Effect", "✒️ Charcoal Sketch Effect", "✒️ Find Edges (Advanced)"]:
        tool_configs = {
            "🖌️ Oil Painting Effect": {"name": "Oil Painting", "spinner_text": "Applying oil painting effect..."},
            "✒️ Charcoal Sketch Effect": {"name": "Charcoal Sketch", "spinner_text": "Applying charcoal sketch effect..."},
            "✒️ Find Edges (Advanced)": {"name": "Find Edges Advanced", "filter": ImageFilter.FIND_EDGES, "spinner_text": "Finding edges..."}
        }
        config = tool_configs[selected_misc_tool]
        tool_name_lower = config['name'].lower().replace(" ", "_")

        with st.expander(selected_misc_tool, expanded=True):
            st.info(f"Apply the {config['name']} effect to your image.")
            
            image_file = st.file_uploader(f"Upload an image for {config['name']}", type=["png", "jpg", "jpeg", "webp"], key=f"{tool_name_lower}_uploader")

            if image_file:
                if f'{tool_name_lower}_img_bytes' not in st.session_state or image_file.getvalue() != st.session_state.get(f'{tool_name_lower}_img_bytes'):
                    st.session_state[f'{tool_name_lower}_img_bytes'] = image_file.getvalue()
                    st.session_state[f'{tool_name_lower}_art_dict'] = None

                original_pil = Image.open(BytesIO(st.session_state[f'{tool_name_lower}_img_bytes']))
                st.image(original_pil, caption="Original Image", use_container_width=True)

                if st.button(f"{selected_misc_tool.split(' ')[0]} Apply Effect", width='stretch'):
                    with st.spinner(config['spinner_text']):
                        try:
                            if config['name'] == "Oil Painting":
                                processed_image = original_pil.filter(ImageFilter.MedianFilter(size=9))
                            elif config['name'] == "Charcoal Sketch":
                                gray = original_pil.convert('L')
                                edges = gray.filter(ImageFilter.FIND_EDGES)
                                processed_image = edges.filter(ImageFilter.SMOOTH_MORE)
                            else: # Find Edges Advanced
                                processed_image = original_pil.filter(ImageFilter.FIND_EDGES)

                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state[f'{tool_name_lower}_art_dict'] = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Effect application failed: {e}")

            if f'{tool_name_lower}_art_dict' in st.session_state and st.session_state[f'{tool_name_lower}_art_dict']:
                st.markdown(f"---"); st.markdown(f"#### ✨ {config['name']} Result")
                result_dict = st.session_state[f'{tool_name_lower}_art_dict']
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Your {tool_name_lower} image")
                st.download_button("💾 Download as .png", result_data, f"{tool_name_lower}_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_{tool_name_lower}_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': f"Image from {config['name']}", 'enhanced_prompt': f"Image created with the {config['name']} utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': f"{config['name']}", 'color_mood': 'N/A', 'lighting': 'N/A', 'description': f"Image created using the {config['name']} feature.", 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_{tool_name_lower}_{image_id}"):
                        add_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite(): add_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite, width='stretch', key=f"fav_{tool_name_lower}_{image_id}")

    elif selected_misc_tool == "🌡️ Color Temperature":
        with st.expander("🌡️ Color Temperature", expanded=True):
            st.info("Adjust the color temperature to make the image warmer (orange) or cooler (blue).")
            
            temp_image_file = st.file_uploader("Upload an image to adjust temperature", type=["png", "jpg", "jpeg", "webp"], key="temp_uploader")

            if temp_image_file:
                if 'temp_img_bytes' not in st.session_state or temp_image_file.getvalue() != st.session_state.get('temp_img_bytes'):
                    st.session_state.temp_img_bytes = temp_image_file.getvalue()
                    st.session_state.temp_art_dict = None

                original_pil_temp = Image.open(BytesIO(st.session_state.temp_img_bytes)).convert("RGB")
                st.image(original_pil_temp, caption="Original Image", use_container_width=True)

                temp_adjust = st.slider("Temperature Adjustment", -100, 100, 0, help="Negative for cooler (blue), positive for warmer (orange).")

                if st.button("🌡️ Apply Temperature", width='stretch'):
                    with st.spinner("Adjusting temperature..."):
                        try:
                            r, g, b = original_pil_temp.split()
                            if temp_adjust > 0: # Warm
                                r = r.point(lambda i: i + temp_adjust * 1.2)
                                b = b.point(lambda i: i - temp_adjust * 0.8)
                            elif temp_adjust < 0: # Cool
                                r = r.point(lambda i: i + temp_adjust * 0.8)
                                b = b.point(lambda i: i - temp_adjust * 1.2)
                            
                            temp_image = Image.merge("RGB", (r, g, b))
                            output_buffer = BytesIO()
                            temp_image.save(output_buffer, format="PNG")
                            st.session_state.temp_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Temperature adjustment failed: {e}")

            if 'temp_art_dict' in st.session_state and st.session_state.temp_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Temperature Adjusted Result")
                result_dict = st.session_state.temp_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your temperature adjusted image")
                st.download_button("💾 Download as .png", result_data, f"temp_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_temp_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_temp_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Color Temperature", 'enhanced_prompt': "Image created with the Color Temperature utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Color Temperature', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Color Temperature feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_temp_{image_id}"):
                        add_temp_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_temp(): add_temp_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_temp, width='stretch', key=f"fav_temp_{image_id}")

    elif selected_misc_tool == "🎲 Add Noise":
        with st.expander("🎲 Add Noise", expanded=True):
            st.info("Add random noise to your image for a grainy, vintage effect.")
            
            noise_image_file = st.file_uploader("Upload an image to add noise", type=["png", "jpg", "jpeg", "webp"], key="noise_uploader")

            if noise_image_file:
                if 'noise_img_bytes' not in st.session_state or noise_image_file.getvalue() != st.session_state.get('noise_img_bytes'):
                    st.session_state.noise_img_bytes = noise_image_file.getvalue()
                    st.session_state.noise_art_dict = None

                original_pil_noise = Image.open(BytesIO(st.session_state.noise_img_bytes)).convert("RGB")
                st.image(original_pil_noise, caption="Original Image", use_container_width=True)

                noise_amount = st.slider("Noise Amount", 0, 100, 20, key="noise_amount")

                if st.button("🎲 Add Noise", width='stretch'):
                    with st.spinner("Adding noise..."):
                        try:
                            img_np = np.array(original_pil_noise, dtype=np.float32)
                            noise = np.random.randn(*img_np.shape) * noise_amount
                            noisy_img_np = np.clip(img_np + noise, 0, 255)
                            noisy_image = Image.fromarray(noisy_img_np.astype('uint8'))

                            output_buffer = BytesIO()
                            noisy_image.save(output_buffer, format="PNG")
                            st.session_state.noise_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Adding noise failed: {e}")

            if 'noise_art_dict' in st.session_state and st.session_state.noise_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Noisy Result")
                result_dict = st.session_state.noise_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your noisy image")
                st.download_button("💾 Download as .png", result_data, f"noisy_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_noise_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_noise_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Add Noise", 'enhanced_prompt': "Image created with the Add Noise utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Add Noise', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Add Noise feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_noise_{image_id}"):
                        add_noise_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_noise(): add_noise_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_noise, width='stretch', key=f"fav_noise_{image_id}")

    elif selected_misc_tool == "📈 Color Curves (Simple)":
        with st.expander("📈 Color Curves (Simple)", expanded=True):
            st.info("Apply a simple S-curve to increase contrast.")
            
            curves_image_file = st.file_uploader("Upload an image to apply curve", type=["png", "jpg", "jpeg", "webp"], key="curves_uploader")

            if curves_image_file:
                if 'curves_img_bytes' not in st.session_state or curves_image_file.getvalue() != st.session_state.get('curves_img_bytes'):
                    st.session_state.curves_img_bytes = curves_image_file.getvalue()
                    st.session_state.curves_art_dict = None

                original_pil_curves = Image.open(BytesIO(st.session_state.curves_img_bytes))
                st.image(original_pil_curves, caption="Original Image", use_container_width=True)

                if st.button("📈 Apply S-Curve", width='stretch'):
                    with st.spinner("Applying curve..."):
                        try:
                            table = [int(255 * (1 / (1 + np.exp(-(i/255 - 0.5) * 10)))) for i in range(256)]
                            curves_image = original_pil_curves.point(table * len(original_pil_curves.getbands()))

                            output_buffer = BytesIO()
                            curves_image.save(output_buffer, format="PNG")
                            st.session_state.curves_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Curve application failed: {e}")

            if 'curves_art_dict' in st.session_state and st.session_state.curves_art_dict:
                st.markdown("---"); st.markdown("#### ✨ S-Curve Result")
                result_dict = st.session_state.curves_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your S-curve adjusted image")
                st.download_button("💾 Download as .png", result_data, f"curves_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_curves_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_curves_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Color Curves", 'enhanced_prompt': "Image created with the Color Curves utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Color Curves', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Color Curves feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_curves_{image_id}"):
                        add_curves_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_curves(): add_curves_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_curves, width='stretch', key=f"fav_curves_{image_id}")

    elif selected_misc_tool == "↔️ Image Resizer":
        with st.expander("↔️ Image Resizer", expanded=True):
            st.info("Resize an image to new dimensions.")
            
            resizer_image_file = st.file_uploader("Upload an image to resize", type=["png", "jpg", "jpeg", "webp"], key="resizer_uploader")

            if resizer_image_file:
                if 'resizer_img_bytes' not in st.session_state or resizer_image_file.getvalue() != st.session_state.get('resizer_img_bytes'):
                    st.session_state.resizer_img_bytes = resizer_image_file.getvalue()
                    st.session_state.resizer_art_dict = None

                original_pil_resizer = Image.open(BytesIO(st.session_state.resizer_img_bytes))
                st.image(original_pil_resizer, caption=f"Original Image ({original_pil_resizer.width}x{original_pil_resizer.height})", use_container_width=True)

                c1, c2 = st.columns(2)
                new_width = c1.number_input("New Width (px)", 1, 4096, original_pil_resizer.width)
                new_height = c2.number_input("New Height (px)", 1, 4096, original_pil_resizer.height)

                if st.button("↔️ Resize Image", width='stretch'):
                    with st.spinner("Resizing..."):
                        try:
                            resized_image = original_pil_resizer.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            output_buffer = BytesIO()
                            resized_image.save(output_buffer, format="PNG")
                            st.session_state.resizer_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Resizing failed: {e}")

            if 'resizer_art_dict' in st.session_state and st.session_state.resizer_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Resized Result")
                result_dict = st.session_state.resizer_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your resized image")
                st.download_button("💾 Download as .png", result_data, f"resized_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_resizer_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_resizer_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Image Resizer", 'enhanced_prompt': "Image created with the Image Resizer utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Image Resizer', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Image Resizer feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_resizer_{image_id}"):
                        add_resizer_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_resizer(): add_resizer_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_resizer, width='stretch', key=f"fav_resizer_{image_id}")

    elif selected_misc_tool == "💧 Create Reflection":
        with st.expander("💧 Create Reflection", expanded=True):
            st.info("Create a faded, vertical reflection of your image.")
            
            reflection_image_file = st.file_uploader("Upload an image to create a reflection", type=["png", "jpg", "jpeg", "webp"], key="reflection_uploader")

            if reflection_image_file:
                if 'reflection_img_bytes' not in st.session_state or reflection_image_file.getvalue() != st.session_state.get('reflection_img_bytes'):
                    st.session_state.reflection_img_bytes = reflection_image_file.getvalue()
                    st.session_state.reflection_art_dict = None

                original_pil_reflection = Image.open(BytesIO(st.session_state.reflection_img_bytes)).convert("RGBA")
                st.image(original_pil_reflection, caption="Original Image", use_container_width=True)

                if st.button("💧 Create Reflection", width='stretch'):
                    with st.spinner("Creating reflection..."):
                        try:
                            w, h = original_pil_reflection.size
                            reflection = original_pil_reflection.transpose(Image.FLIP_TOP_BOTTOM)
                            gradient = Image.new('L', (1, h), 0)
                            for y in range(h):
                                gradient.putpixel((0, y), int(255 * (1 - y / h)))
                            alpha = gradient.resize((w, h))
                            reflection.putalpha(alpha)
                            
                            combined = Image.new('RGBA', (w, h * 2), (255, 255, 255, 0))
                            combined.paste(original_pil_reflection, (0, 0))
                            combined.paste(reflection, (0, h))

                            output_buffer = BytesIO()
                            combined.convert("RGB").save(output_buffer, format="PNG")
                            st.session_state.reflection_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Reflection creation failed: {e}")

            if 'reflection_art_dict' in st.session_state and st.session_state.reflection_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Reflection Result")
                result_dict = st.session_state.reflection_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your image with reflection")
                st.download_button("💾 Download as .png", result_data, f"reflection_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_reflection_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_reflection_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Create Reflection", 'enhanced_prompt': "Image created with the Create Reflection utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Create Reflection', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Create Reflection feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_reflection_{image_id}"):
                        add_reflection_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_reflection(): add_reflection_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_reflection, width='stretch', key=f"fav_reflection_{image_id}")

    elif selected_misc_tool == "💥 Comic Book Effect":
        with st.expander("💥 Comic Book Effect", expanded=True):
            st.info("Transform your image into a classic comic book panel with outlines and halftone dots.")
            
            comic_image_file = st.file_uploader("Upload an image for the comic book effect", type=["png", "jpg", "jpeg", "webp"], key="comic_uploader")

            if comic_image_file:
                if 'comic_img_bytes' not in st.session_state or comic_image_file.getvalue() != st.session_state.get('comic_img_bytes'):
                    st.session_state.comic_img_bytes = comic_image_file.getvalue()
                    st.session_state.comic_art_dict = None

                original_pil_comic = Image.open(BytesIO(st.session_state.comic_img_bytes)).convert("RGB")
                st.image(original_pil_comic, caption="Original Image", use_container_width=True)

                if st.button("💥 Apply Comic Book Effect", width='stretch'):
                    with st.spinner("Inking and coloring..."):
                        try:
                            # 1. Edge detection for outlines
                            edges = original_pil_comic.convert('L').filter(ImageFilter.FIND_EDGES)
                            edges = ImageOps.invert(edges)
                            
                            # 2. Posterize for flat colors
                            posterized = ImageOps.posterize(original_pil_comic, 3)

                            # 3. Combine outlines and colors
                            comic_image = Image.blend(posterized, edges.convert('RGB'), alpha=0.3)

                            output_buffer = BytesIO()
                            comic_image.save(output_buffer, format="PNG")
                            st.session_state.comic_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Comic book effect failed: {e}")

            if 'comic_art_dict' in st.session_state and st.session_state.comic_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Comic Book Result")
                result_dict = st.session_state.comic_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your comic book image")
                st.download_button("💾 Download as .png", result_data, f"comic_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_comic_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_comic_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Comic Book Effect", 'enhanced_prompt': "Image created with the Comic Book Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Comic Book Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Comic Book Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_comic_{image_id}"):
                        add_comic_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_comic(): add_comic_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_comic, width='stretch', key=f"fav_comic_{image_id}")

    elif selected_misc_tool == "🪩 Chromatic Aberration":
        with st.expander("🪩 Chromatic Aberration", expanded=True):
            st.info("Create a retro RGB split effect by shifting the color channels.")
            
            ca_image_file = st.file_uploader("Upload an image for chromatic aberration", type=["png", "jpg", "jpeg", "webp"], key="ca_uploader")

            if ca_image_file:
                if 'ca_img_bytes' not in st.session_state or ca_image_file.getvalue() != st.session_state.get('ca_img_bytes'):
                    st.session_state.ca_img_bytes = ca_image_file.getvalue()
                    st.session_state.ca_art_dict = None

                original_pil_ca = Image.open(BytesIO(st.session_state.ca_img_bytes)).convert("RGB")
                st.image(original_pil_ca, caption="Original Image", use_container_width=True)

                shift_amount = st.slider("Shift Amount (pixels)", 1, 50, 10, key="ca_shift")

                if st.button("🪩 Apply RGB Split", width='stretch'):
                    with st.spinner("Splitting channels..."):
                        try:
                            r, g, b = original_pil_ca.split()
                            r_shifted = Image.new('L', original_pil_ca.size)
                            r_shifted.paste(r, (-shift_amount, 0))
                            b_shifted = Image.new('L', original_pil_ca.size)
                            b_shifted.paste(b, (shift_amount, 0))
                            ca_image = Image.merge("RGB", (r_shifted, g, b_shifted))

                            output_buffer = BytesIO()
                            ca_image.save(output_buffer, format="PNG")
                            st.session_state.ca_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Chromatic aberration failed: {e}")

            if 'ca_art_dict' in st.session_state and st.session_state.ca_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Chromatic Aberration Result")
                result_dict = st.session_state.ca_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your RGB split image")
                st.download_button("💾 Download as .png", result_data, f"ca_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_ca_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_ca_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Chromatic Aberration", 'enhanced_prompt': "Image created with the Chromatic Aberration utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Chromatic Aberration', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Chromatic Aberration feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_ca_{image_id}"):
                        add_ca_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_ca(): add_ca_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_ca, width='stretch', key=f"fav_ca_{image_id}")

    elif selected_misc_tool == "🤏 Tilt-Shift (Miniature) Effect":
        with st.expander("🤏 Tilt-Shift (Miniature) Effect", expanded=True):
            st.info("Create a 'miniature world' effect by blurring the top and bottom of the image.")
            
            tilt_image_file = st.file_uploader("Upload an image for tilt-shift effect", type=["png", "jpg", "jpeg", "webp"], key="tilt_uploader")

            if tilt_image_file:
                if 'tilt_img_bytes' not in st.session_state or tilt_image_file.getvalue() != st.session_state.get('tilt_img_bytes'):
                    st.session_state.tilt_img_bytes = tilt_image_file.getvalue()
                    st.session_state.tilt_art_dict = None

                original_pil_tilt = Image.open(BytesIO(st.session_state.tilt_img_bytes)).convert("RGB")
                st.image(original_pil_tilt, caption="Original Image", use_container_width=True)

                focus_point = st.slider("Focus Point (Vertical %)", 0, 100, 50, key="tilt_focus")
                focus_width = st.slider("Focus Width (%)", 1, 100, 20, key="tilt_width")

                if st.button("🤏 Apply Tilt-Shift", width='stretch'):
                    with st.spinner("Creating miniature effect..."):
                        try:
                            w, h = original_pil_tilt.size
                            blurred = original_pil_tilt.filter(ImageFilter.GaussianBlur(5))
                            mask = Image.new('L', (w, h), 0)
                            draw = ImageDraw.Draw(mask)
                            
                            focus_start = h * (focus_point - focus_width / 2) / 100
                            focus_end = h * (focus_point + focus_width / 2) / 100
                            
                            for y in range(h):
                                if focus_start <= y <= focus_end:
                                    val = 255
                                else:
                                    dist = min(abs(y - focus_start), abs(y - focus_end))
                                    val = max(0, 255 - int(dist * 2))
                                draw.line([(0, y), (w, y)], fill=val)

                            tilt_image = Image.composite(original_pil_tilt, blurred, mask)

                            output_buffer = BytesIO()
                            tilt_image.save(output_buffer, format="PNG")
                            st.session_state.tilt_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Tilt-shift effect failed: {e}")

            if 'tilt_art_dict' in st.session_state and st.session_state.tilt_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Tilt-Shift Result")
                result_dict = st.session_state.tilt_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your tilt-shift image")
                st.download_button("💾 Download as .png", result_data, f"tilt_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_tilt_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_tilt_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Tilt-Shift Effect", 'enhanced_prompt': "Image created with the Tilt-Shift Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Tilt-Shift Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Tilt-Shift Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_tilt_{image_id}"):
                        add_tilt_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_tilt(): add_tilt_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_tilt, width='stretch', key=f"fav_tilt_{image_id}")

    elif selected_misc_tool == "📐 Blueprint Effect":
        with st.expander("📐 Blueprint Effect", expanded=True):
            st.info("Transform your image into a stylized architectural blueprint.")
            
            blueprint_image_file = st.file_uploader("Upload an image for blueprint effect", type=["png", "jpg", "jpeg", "webp"], key="blueprint_uploader")

            if blueprint_image_file:
                if 'blueprint_img_bytes' not in st.session_state or blueprint_image_file.getvalue() != st.session_state.get('blueprint_img_bytes'):
                    st.session_state.blueprint_img_bytes = blueprint_image_file.getvalue()
                    st.session_state.blueprint_art_dict = None

                original_pil_blueprint = Image.open(BytesIO(st.session_state.blueprint_img_bytes)).convert("RGB")
                st.image(original_pil_blueprint, caption="Original Image", use_container_width=True)

                if st.button("📐 Apply Blueprint Effect", width='stretch'):
                    with st.spinner("Drafting blueprint..."):
                        try:
                            edges = original_pil_blueprint.convert('L').filter(ImageFilter.CONTOUR)
                            inverted_edges = ImageOps.invert(edges)
                            blueprint_image = ImageOps.colorize(inverted_edges, black="#002266", white="#FFFFFF")

                            output_buffer = BytesIO()
                            blueprint_image.save(output_buffer, format="PNG")
                            st.session_state.blueprint_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Blueprint effect failed: {e}")

            if 'blueprint_art_dict' in st.session_state and st.session_state.blueprint_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Blueprint Result")
                result_dict = st.session_state.blueprint_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your blueprint image")
                st.download_button("💾 Download as .png", result_data, f"blueprint_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_blueprint_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_blueprint_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Blueprint Effect", 'enhanced_prompt': "Image created with the Blueprint Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Blueprint Effect', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Blueprint Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_blueprint_{image_id}"):
                        add_blueprint_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_blueprint(): add_blueprint_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_blueprint, width='stretch', key=f"fav_blueprint_{image_id}")

    elif selected_misc_tool == "🕶️ Anaglyph 3D Effect":
        with st.expander("🕶️ Anaglyph 3D Effect", expanded=True):
            st.info("Create a vintage red-cyan 3D effect. (Requires 3D glasses to view properly).")
            
            anaglyph_image_file = st.file_uploader("Upload an image for anaglyph effect", type=["png", "jpg", "jpeg", "webp"], key="anaglyph_uploader")

            if anaglyph_image_file:
                if 'anaglyph_img_bytes' not in st.session_state or anaglyph_image_file.getvalue() != st.session_state.get('anaglyph_img_bytes'):
                    st.session_state.anaglyph_img_bytes = anaglyph_image_file.getvalue()
                    st.session_state.anaglyph_art_dict = None

                original_pil_anaglyph = Image.open(BytesIO(st.session_state.anaglyph_img_bytes)).convert("RGB")
                st.image(original_pil_anaglyph, caption="Original Image", use_container_width=True)

                shift = st.slider("3D Shift Amount (pixels)", 1, 20, 5, key="anaglyph_shift")

                if st.button("🕶️ Apply Anaglyph 3D", width='stretch'):
                    with st.spinner("Creating 3D effect..."):
                        try:
                            r, g, b = original_pil_anaglyph.split()
                            left_img = Image.merge('RGB', (Image.new('L', r.size, 0), g, b))
                            right_img = Image.new('RGB', original_pil_anaglyph.size)
                            right_img.paste(r, (-shift, 0))
                            anaglyph_image = Image.blend(left_img, right_img, 0.5)

                            output_buffer = BytesIO()
                            anaglyph_image.save(output_buffer, format="PNG")
                            st.session_state.anaglyph_art_dict = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Anaglyph effect failed: {e}")

            if 'anaglyph_art_dict' in st.session_state and st.session_state.anaglyph_art_dict:
                st.markdown("---"); st.markdown("#### ✨ Anaglyph 3D Result")
                result_dict = st.session_state.anaglyph_art_dict
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption="Your anaglyph 3D image")
                st.download_button("💾 Download as .png", result_data, f"anaglyph_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_anaglyph_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_anaglyph_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': "Image from Anaglyph 3D Effect", 'enhanced_prompt': "Image created with the Anaglyph 3D Effect utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Anaglyph 3D', 'color_mood': 'N/A', 'lighting': 'N/A', 'description': 'Image created using the Anaglyph 3D Effect feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_anaglyph_{image_id}"):
                        add_anaglyph_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite_anaglyph(): add_anaglyph_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite_anaglyph, width='stretch', key=f"fav_anaglyph_{image_id}")

    elif selected_misc_tool in ["🎨 Pop Art Effect", "☀️ Light Leak Effect", "🌙 Night Vision Effect", "📺 Scanlines (CRT) Effect", "🧊 Frosted Glass Effect"]:
        tool_configs = {
            "🎨 Pop Art Effect": {"name": "Pop Art", "spinner_text": "Creating Pop Art..."},
            "☀️ Light Leak Effect": {"name": "Light Leak", "spinner_text": "Adding light leak..."},
            "🌙 Night Vision Effect": {"name": "Night Vision", "spinner_text": "Enabling night vision..."},
            "📺 Scanlines (CRT) Effect": {"name": "Scanlines", "spinner_text": "Adding scanlines..."},
            "🧊 Frosted Glass Effect": {"name": "Frosted Glass", "spinner_text": "Frosting glass..."}
        }
        config = tool_configs[selected_misc_tool]
        tool_name_lower = config['name'].lower().replace(" ", "_")

        with st.expander(selected_misc_tool, expanded=True):
            st.info(f"Apply a {config['name']} effect to your image.")
            
            image_file = st.file_uploader(f"Upload an image for {config['name']} effect", type=["png", "jpg", "jpeg", "webp"], key=f"{tool_name_lower}_uploader")

            if image_file:
                if f'{tool_name_lower}_img_bytes' not in st.session_state or image_file.getvalue() != st.session_state.get(f'{tool_name_lower}_img_bytes'):
                    st.session_state[f'{tool_name_lower}_img_bytes'] = image_file.getvalue()
                    st.session_state[f'{tool_name_lower}_art_dict'] = None

                original_pil = Image.open(BytesIO(st.session_state[f'{tool_name_lower}_img_bytes'])).convert("RGB")
                st.image(original_pil, caption="Original Image", use_container_width=True)

                if st.button(f"{selected_misc_tool.split(' ')[0]} Apply Effect", width='stretch'):
                    with st.spinner(config['spinner_text']):
                        try:
                            w, h = original_pil.size
                            if config['name'] == "Pop Art":
                                colors = [ImageOps.colorize(original_pil.convert('L'), black=c1, white=c2) for c1, c2 in [("#0000FF", "#FFFF00"), ("#FF0000", "#00FFFF"), ("#00FF00", "#FF00FF"), ("#FFFF00", "#0000FF")]]
                                processed_image = Image.new('RGB', (w*2, h*2))
                                processed_image.paste(colors[0].resize((w,h)), (0,0))
                                processed_image.paste(colors[1].resize((w,h)), (w,0))
                                processed_image.paste(colors[2].resize((w,h)), (0,h))
                                processed_image.paste(colors[3].resize((w,h)), (w,h))
                            elif config['name'] == "Light Leak":
                                gradient = Image.new('L', (w, h), 0)
                                draw = ImageDraw.Draw(gradient)
                                for i in range(h):
                                    draw.line([(0, i), (w, i)], fill=int(255 * (i/h)**2))
                                leak_color = Image.new('RGB', (w, h), '#FF5733')
                                leak = Image.composite(leak_color, Image.new('RGB', (w,h), (0,0,0)), gradient)
                                processed_image = Image.blend(original_pil, leak, alpha=0.3)
                            elif config['name'] == "Night Vision":
                                gray = original_pil.convert('L')
                                processed_image = ImageOps.colorize(gray, black="#0A2A0A", white="#30FF30")
                                noise = np.random.randint(-20, 20, (h, w, 3), dtype='int16')
                                processed_image = Image.fromarray(np.clip(np.array(processed_image) + noise, 0, 255).astype('uint8'))
                            elif config['name'] == "Scanlines":
                                processed_image = original_pil.copy()
                                draw = ImageDraw.Draw(processed_image)
                                for y in range(0, h, 2):
                                    draw.line([(0, y), (w, y)], fill=(0, 0, 0, 50))
                            elif config['name'] == "Frosted Glass":
                                small = original_pil.resize((w//20, h//20), Image.Resampling.BILINEAR)
                                processed_image = small.resize(original_pil.size, Image.Resampling.NEAREST)
                                processed_image = processed_image.filter(ImageFilter.GaussianBlur(2))

                            output_buffer = BytesIO()
                            processed_image.save(output_buffer, format="PNG")
                            st.session_state[f'{tool_name_lower}_art_dict'] = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Effect application failed: {e}")

            if f'{tool_name_lower}_art_dict' in st.session_state and st.session_state[f'{tool_name_lower}_art_dict']:
                st.markdown(f"---"); st.markdown(f"#### ✨ {config['name']} Result")
                result_dict = st.session_state[f'{tool_name_lower}_art_dict']
                result_data, image_id = result_dict['data'], result_dict['id']
                st.image(result_data, use_container_width=True, caption=f"Your {tool_name_lower} image")
                st.download_button("💾 Download as .png", result_data, f"{tool_name_lower}_art_{int(time.time())}.png", "image/png", width='stretch', key=f"download_{tool_name_lower}_{image_id}")
                b_col1, b_col2 = st.columns(2)
                def add_to_gallery():
                    if not any(img['id'] == image_id for img in st.session_state.images):
                        st.session_state.images.append({'id': image_id, 'image_data': result_data, 'original_prompt': f"Image from {config['name']}", 'enhanced_prompt': f"Image created with the {config['name']} utility.", 'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': f"{config['name']}", 'color_mood': 'N/A', 'lighting': 'N/A', 'description': f"Image created using the {config['name']} feature.", 'aspect_ratio': 'N/A', 'quality_level': 'N/A'})
                        save_image_to_db(st.session_state.images[-1]); st.toast("✅ Added to gallery!")
                with b_col1:
                    is_in_gallery = any(img['id'] == image_id for img in st.session_state.images)
                    if st.button("🖼️ Add to Gallery", width='stretch', disabled=is_in_gallery, key=f"gallery_{tool_name_lower}_{image_id}"):
                        add_to_gallery(); st.rerun()
                with b_col2:
                    is_favorited = image_id in st.session_state.favorites; star_icon = "★" if is_favorited else "☆"
                    def handle_favorite(): add_to_gallery(); toggle_and_save_favorite(image_id)
                    st.button(f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", on_click=handle_favorite, width='stretch', key=f"fav_{tool_name_lower}_{image_id}")

    # --- END: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # --- END: SURPRISE ME - RANDOM PROMPT GENERATOR ---


    # Quick actions will still only appear after the first image is generated.
    if st.session_state.images:
        st.markdown("### 🧰 Quick Actions")


        # --- START: PROMPT HISTORY & FAVORITES FEATURE ---

        # 1. Prompt History
        # 1. Prompt History
        with st.expander("📜 Prompt History"):
            if not st.session_state.prompt_history:
                st.info("Your recent prompts will appear here.")
            else:
                # --- ADVANCED PROMPT HISTORY CONTROLS ---
                with st.container(border=True):
                    st.markdown("##### 🔬 Filter & Sort History")
                    
                    # 1. Search Bar for History
                    search_query_hist = st.text_input(
                        "🔍 Search by Keyword",
                        placeholder="e.g., majestic, neon, painting...",
                        key="prompt_hist_search"
                    )
                    
                    # 2. Sort Order for History
                    sort_order_hist = st.selectbox(
                        "⏳ Sort History",
                        ["Newest First", "Oldest First"],
                        key="prompt_hist_sort"
                    )

                # --- FILTERING AND SORTING LOGIC ---
                
                # Start with the full history
                history_list = st.session_state.prompt_history
                
                # Apply search filter
                if search_query_hist:
                    history_list = [
                        p for p in history_list if search_query_hist.lower() in p.lower()
                    ]

                # Apply sorting
                # New prompts are inserted at the start, so the list is already "Newest First"
                if sort_order_hist == "Oldest First":
                    display_list = list(reversed(history_list))
                else: # "Newest First"
                    display_list = history_list
                
                st.markdown("---")
                st.markdown(f"**{len(display_list)}** prompt(s) found.")

                if not display_list:
                    st.info("No prompts match your current filter criteria.")
                else:
                    def apply_historical_prompt(prompt_text):
                        st.session_state.main_prompt = prompt_text
                    
                    # Display the filtered and sorted prompts
                    # Display the filtered and sorted prompts
                    for prompt in display_list:
                        with st.container(border=True):
                            st.markdown(f"<small>{prompt[:100]}...</small>", unsafe_allow_html=True)
                            
                            # Create columns for "Use" and "Remove" buttons
                            use_col, remove_col = st.columns([3, 1])

                            with use_col:
                                st.button(
                                    "✍️ Use This Prompt", 
                                    key=f"hist_use_{hash(prompt)}", 
                                    on_click=apply_historical_prompt, 
                                    args=(prompt,), 
                                    use_container_width=True
                                )
                            with remove_col:
                                st.button(
                                    "🗑️",
                                    key=f"hist_remove_{hash(prompt)}",
                                    on_click=remove_prompt_from_history,
                                    args=(prompt,),
                                    use_container_width=True,
                                    help="Remove this prompt"
                                )
                
                st.markdown("---")
                if st.button("Clear Entire History", use_container_width=True):
                    st.session_state.prompt_history = []
                    save_prompt_history_to_db()
                    st.rerun()

        # 2. Favorites
        # 2. Favorites
        with st.expander("⭐ Favorites"):
            if not st.session_state.favorites:
                st.info("Your favorite images will appear here. Click the ☆ icon on an image to save it.")
            else:
                # First, get the list of all favorited image data
                favorited_images = [
                    img for img in st.session_state.images if img['id'] in st.session_state.favorites
                ]

                # --- ADVANCED FAVORITES CONTROLS ---
                with st.container(border=True):
                    st.markdown("##### 🔬 Filter & Sort Favorites")
                    
                    # 1. Search Bar for Favorites
                    search_query_fav = st.text_input(
                        "🔍 Search Favorites by Prompt",
                        placeholder="e.g., cyberpunk, serene...",
                        key="fav_search"
                    )

                    # 2. Filter by Style (options are generated only from favorites)
                    fav_styles = sorted(list(set(
                        img.get('style_used', 'N/A') for img in favorited_images
                    )))
                    selected_styles_fav = st.multiselect(
                        "🎨 Filter Favorites by Style",
                        options=fav_styles,
                        key="fav_style_filter"
                    )
                    
                    # 3. Sort Order for Favorites
                    sort_order_fav = st.selectbox(
                        "⏳ Sort Favorites by",
                        ["Newest First", "Oldest First"],
                        key="fav_sort"
                    )

                # --- FILTERING LOGIC ---
                filtered_favorites = favorited_images
                
                if search_query_fav:
                    filtered_favorites = [
                        img for img in filtered_favorites
                        if search_query_fav.lower() in img.get('original_prompt', '').lower() or \
                           search_query_fav.lower() in img.get('enhanced_prompt', '').lower()
                    ]
                
                if selected_styles_fav:
                    filtered_favorites = [
                        img for img in filtered_favorites
                        if img.get('style_used') in selected_styles_fav
                    ]

                # --- SORTING & DISPLAY LOGIC ---
                st.markdown("---")
                
                # Sort the filtered list based on generation time
                if sort_order_fav == "Newest First":
                    display_list = sorted(filtered_favorites, key=lambda x: x.get('generation_time', ''), reverse=True)
                else: # "Oldest First"
                    display_list = sorted(filtered_favorites, key=lambda x: x.get('generation_time', ''))

                st.markdown(f"**{len(display_list)}** favorite(s) found.")

                if not display_list:
                    st.info("No favorites match your current filter criteria.")
                else:
                    # Create a grid for thumbnails
                    # Create a grid for thumbnails
                    cols = st.columns(3)
                    for i, fav_img_data in enumerate(display_list):
                        with cols[i % 3]:
                            thumb = Image.open(BytesIO(fav_img_data['image_data']))
                            thumb.thumbnail((150, 150))
                            
                            # Make the image itself clickable to view
                            if st.button(f"{i}", key=f"fav_view_{fav_img_data['id']}", use_container_width=True):
                                st.session_state.current_image = fav_img_data
                                st.rerun()
                            # Display the image inside the button area by targeting the container
                            st.image(thumb, use_container_width=True)
                            
                            # Add a dedicated unfavorite button below the image
                            st.button(
                                "🗑️", 
                                key=f"unfav_sidebar_{fav_img_data['id']}", 
                                on_click=toggle_and_save_favorite, 
                                args=(fav_img_data['id'],),
                                use_container_width=True
                            )

                st.markdown("---")
                if st.button("🗑️ Clear All Favorites", use_container_width=True, key="clear_favorites"):
                    st.session_state.favorites = []
                    save_favorites_to_db()
                    st.rerun()

        # --- START: NEW QUICK ACTION TOOLS ---
        with st.expander("🎨 Quick Color Palette"):
            st.info("Quickly extract a color palette from an image.")
            palette_image_file_qa = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"], key="palette_uploader_qa")

            if palette_image_file_qa:
                if 'palette_img_bytes_qa' not in st.session_state or palette_image_file_qa.getvalue() != st.session_state.get('palette_img_bytes_qa'):
                    st.session_state.palette_img_bytes_qa = palette_image_file_qa.getvalue()
                    st.session_state.palette_result_qa = None

                num_colors_qa = st.slider("Number of Colors", 2, 8, 5, key="palette_num_colors_qa")

                if st.button("🎨 Extract Palette", width='stretch', key="palette_btn_qa"):
                    with st.spinner("Analyzing colors..."):
                        try:
                            original_pil_palette_qa = Image.open(BytesIO(st.session_state.palette_img_bytes_qa))
                            img_resized = original_pil_palette_qa.resize((100, 100))
                            img_array = np.array(img_resized.convert("RGB"))
                            pixels = img_array.reshape(-1, 3)
                            kmeans = KMeans(n_clusters=num_colors_qa, random_state=42, n_init='auto').fit(pixels)
                            dominant_colors = kmeans.cluster_centers_.astype(int)
                            hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dominant_colors]
                            st.session_state.palette_result_qa = hex_colors
                        except Exception as e:
                            st.error(f"Palette extraction failed: {e}")

            if 'palette_result_qa' in st.session_state and st.session_state.palette_result_qa:
                st.markdown("##### ✨ Extracted Palette")
                hex_colors_qa = st.session_state.palette_result_qa
                cols_qa = st.columns(len(hex_colors_qa))
                for i, hex_color in enumerate(hex_colors_qa):
                    with cols_qa[i]:
                        st.markdown(f'<div style="background-color: {hex_color}; height: 40px; width: 100%; border-radius: 4px;"></div>', unsafe_allow_html=True)
                        st.code(hex_color, language=None)

        with st.expander("✏️ Quick Sketch Converter"):
            st.info("Quickly convert an image into a pencil sketch.")
            sketch_image_file_qa = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "webp"], key="sketch_uploader_qa")

            if sketch_image_file_qa:
                if 'sketch_img_bytes_qa' not in st.session_state or sketch_image_file_qa.getvalue() != st.session_state.get('sketch_img_bytes_qa'):
                    st.session_state.sketch_img_bytes_qa = sketch_image_file_qa.getvalue()
                    st.session_state.sketch_art_dict_qa = None

                if st.button("✏️ Generate Sketch", width='stretch', key="sketch_btn_qa"):
                    with st.spinner("Sketching..."):
                        try:
                            original_pil_sketch_qa = Image.open(BytesIO(st.session_state.sketch_img_bytes_qa))
                            grayscale_image = original_pil_sketch_qa.convert("L")
                            inverted_image = ImageOps.invert(grayscale_image)
                            blurred_image = inverted_image.filter(ImageFilter.GaussianBlur(radius=5))
                            
                            grayscale_np = np.array(grayscale_image, dtype=np.float32)
                            blurred_np = np.array(blurred_image, dtype=np.float32)
                            
                            epsilon = 1e-6
                            sketch_np = (grayscale_np * 255.0) / (255.0 - blurred_np + epsilon)
                            sketch_np = np.clip(sketch_np, 0, 255)
                            
                            sketch_image = Image.fromarray(sketch_np.astype('uint8'))
                            
                            output_buffer = BytesIO()
                            sketch_image.save(output_buffer, format="PNG")
                            st.session_state.sketch_art_dict_qa = {"id": str(uuid.uuid4()), "data": output_buffer.getvalue()}
                        except Exception as e:
                            st.error(f"Sketch conversion failed: {e}")

            if 'sketch_art_dict_qa' in st.session_state and st.session_state.sketch_art_dict_qa:
                st.markdown("---")
                st.markdown("##### ✨ Sketch Result")
                result_dict = st.session_state.sketch_art_dict_qa
                st.image(result_dict['data'], use_container_width=True)
                if st.button("View in Main Panel", key=f"view_sketch_qa_{result_dict['id']}", width='stretch'):
                    st.session_state.current_image = {
                        'id': result_dict['id'], 'image_data': result_dict['data'],
                        'original_prompt': "Image from Quick Sketch", 'enhanced_prompt': "Image created with the Quick Sketch utility.",
                        'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"), 'style_used': 'Pencil Sketch', 'color_mood': 'N/A', 'lighting': 'N/A',
                        'description': 'Image created using the Quick Sketch Converter feature.', 'aspect_ratio': 'N/A', 'quality_level': 'N/A'
                    }
                    if not any(img['id'] == result_dict['id'] for img in st.session_state.images):
                        st.session_state.images.append(st.session_state.current_image)
                        save_image_to_db(st.session_state.current_image)
                    st.rerun()
        # --- END: NEW QUICK ACTION TOOLS ---



        # --- START: REVISED QUICK ACTION BUTTONS ---
        def set_random_prompt():
            """Generates and sets a full random prompt."""
            subjects = [
                "A majestic dragon soaring over a volcanic landscape", "An ancient tree spirit with glowing eyes",
                "A celestial fox with nine tails, leaping through stars", "A forgotten library in the clouds",
                "A futuristic city skyline at sunset", "A robot gardener tending to glowing alien plants",
                "A samurai warrior meditating under a cherry blossom tree", "A hidden waterfall oasis in a lush jungle",
                "A clock melting over a branch, in the style of Dali", "An old watchmaker in his workshop"
            ]
            details = [
                "in the style of a classical oil painting", "as a vibrant watercolor illustration",
                "in the style of Hayao Miyazaki", "as a detailed charcoal sketch",
                "with dramatic, cinematic lighting", "with an ethereal, otherworldly glow",
                "in vibrant, rich, saturated colors", "rendered in Unreal Engine 5, hyperrealistic"
            ]
            st.session_state.main_prompt = f"{random.choice(subjects)}, {random.choice(details)}"

        st.button("🎲 Surprise Me! (Full Prompt)", on_click=set_random_prompt, use_container_width=True, help="Generate a completely new random prompt.")

        def reuse_current_prompt():
            """Copies the prompt from the current image to the main prompt input."""
            if st.session_state.current_image:
                reused_prompt = st.session_state.current_image.get('original_prompt', '')
                if reused_prompt:
                    st.session_state.main_prompt = reused_prompt
                else:
                    st.warning("The current image has no prompt to re-use.")
            else:
                st.warning("No image is currently being viewed.")

        st.button("🔄 Re-use Prompt", on_click=reuse_current_prompt, use_container_width=True, help="Copy the prompt from the currently viewed image back to the input box.")
        # --- END: REVISED QUICK ACTION BUTTONS ---
        
        
        if st.button("🎲 Random Style", use_container_width=True):
            import random
            random_category = random.choice(list(STYLE_CATEGORIES.keys()))
            random_style = random.choice(STYLE_CATEGORIES[random_category])
            st.session_state.temp_style = f"{random_category}: {random_style}"
            st.rerun()



        
        if hasattr(st.session_state, 'temp_style'):
            st.markdown(f"**Suggested**: {st.session_state.temp_style}")
        
        if st.button("📊 Gallery Stats", use_container_width=True):
            st.markdown(f"""
            <div class="info-box">
            <strong>📈 Your Stats:</strong><br>
            • Images Generated: {len(st.session_state.images)}<br>
            • Most Used Style: {selected_style}<br>
            • Session Started: {time.strftime('%H:%M')}
            </div>
            """, unsafe_allow_html=True)


# Footer
st.markdown("---")

# 📸 Glimpses from the Gallery – Crafted with love & AI magic 💖

st.markdown("""
<h3 style="
    text-align: center;
    background-image: linear-gradient(90deg, #ff6ec4, #7873f5, #4ade80, #facc15, #f87171, #ff6ec4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    padding: 1rem 0;
">
 Glimpses from the Gallery – Crafted with AI 
</h3>
""", unsafe_allow_html=True)


# --- START: RANDOM GALLERY IMAGE DISPLAY ---

# Consolidate all your image filenames into one list
# gallery_images = [
  #  "k3.jpg", "k2.jpg", "k6.jpg", "k7.jpg", "k19.jpg", "k8.jpg", 
 #   "k4.jpg", "k16.jpg", "k13.jpg", "k14.jpg", "k17.jpg", "k1.jpg","k10.jpg","k9.jpg","k12.jpg","k18.jpg",
#]

#st.sidebar.image("k15.jpg", use_container_width=True)


# Select one image at random from the list


# Display the randomly selected image
#st.image("k19.jpg", use_container_width=True)

# --- END: RANDOM GALLERY IMAGE DISPLAY ---


st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
    <p>✨ Powered by Google Gemini Flash • Created with ❤️ for artists and dreamers</p>
    <p style="font-size: 0.8rem;">Transform your imagination into reality with AI-powered artistry</p>
</div>
""", unsafe_allow_html=True)
