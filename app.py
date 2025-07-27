import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageFilter, ImageOps, ImageDraw
from io import BytesIO
import base64
import json
from gtts import gTTS
import time
import random
import uuid
import numpy as np
from sklearn.cluster import KMeans
# --- START: DATABASE PERSISTENCE SETUP ---
import os
import base64
from tinydb import TinyDB, Query


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

# Create a data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Initialize the database and its tables
db = TinyDB('data/gallery_db.json')
images_table = db.table('images')
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



st.sidebar.image("k5.jpg", use_container_width=True)



# --- START: MODIFIED SESSION STATE INITIALIZATION ---

# Initialize session state and load data only on the first run of a new session
if 'initialized' not in st.session_state:
    st.session_state.initialized = True # Mark as initialized immediately

    # Load all persistent data from the database
    load_data_from_db()

    # Set the current image to the last one in the gallery if it exists
    st.session_state.current_image = st.session_state.images[-1] if st.session_state.images else None

    # Initialize non-persistent state variables that reset with each session
    st.session_state.prompt_history = []
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
        background: linear-gradient(
            180deg,
            rgba(26, 26, 46, 0.95) 0%,
            rgba(10, 10, 15, 0.98) 100%
        );
        backdrop-filter: blur(24px);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
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


st.image("k11.jpg", use_container_width=True)





# Load secrets with error handling
try:
    gemini_api_key = st.secrets["gemini_api_key"]
    client = genai.Client(api_key=gemini_api_key)
except Exception as e:
    st.markdown('<div class="error-box">❌ API key configuration error. Please check your secrets.toml file.</div>', unsafe_allow_html=True)
    st.stop()

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
            for img_data in display_list:
                # Using a unique ID for the key is more robust with filtering
                img_id = img_data['id']
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        img = Image.open(BytesIO(img_data['image_data']))
                        img.thumbnail((80, 80))
                        st.image(img, use_container_width=True)
                    
                    with col2:
                        # Display the prompt for context
                        prompt_summary = img_data.get('original_prompt', 'No Prompt')[:50]
                        st.markdown(f"<small>*{prompt_summary}...*</small>", unsafe_allow_html=True)
                        
                        if st.button("View Image", key=f"view_{img_id}", use_container_width=True):
                            st.session_state.current_image = img_data
                            st.rerun()

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
                # Clear any previously displayed variations for a clean slate
              #  if 'newly_generated_variations' in st.session_state:
               #     st.session_state.newly_generated_variations = None
                
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
                
                try:
                    # Simulate progress
                    status_text.text("🎨 Initializing AI canvas...")
                    progress_bar.progress(20)
                    time.sleep(0.5)
                    
                    status_text.text("🖌️ Mixing digital colors...")
                    progress_bar.progress(40)
                    time.sleep(0.5)
                    
                    status_text.text("✨ Creating your masterpiece...")
                    progress_bar.progress(60)
                    
                    # Generate image
                    # --- CORRECTED CODE ---
                    # Build the contents list for the API call
                    generation_contents = [enhanced_prompt]
                    
                    # Add the negative prompt if it exists
                    if negative_prompt:
                        generation_contents.append(f"Negative prompt: {negative_prompt}")

                    # Generate image
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp-image-generation",
                        contents=generation_contents, # Use the new list here
                        config=types.GenerateContentConfig(
                            response_modalities=["text", "image"]
                        )
                    )
                    # --- END OF CORRECTION ---
                    
                    progress_bar.progress(80)
                    status_text.text("🎭 Adding final touches...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(100)
                    status_text.text("🎉 Masterpiece complete!")
                    
                    # Process response
                    image_data = None
                    description = ""
                    
                    for part in response.candidates[0].content.parts:
                        if part.text:
                            description = part.text
                        elif part.inline_data:
                            image_data = part.inline_data.data
                    
                    if image_data:
                        # Create image metadata
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
                        
                        # Add to gallery and set as current
                        st.session_state.images.append(image_metadata)
                        save_image_to_db(image_metadata)

                        st.session_state.current_image = image_metadata
                        
                        
                        # Clear progress
                        progress_container.empty()
                        
                        # Success message
                        st.markdown('<div class="success-box">🎉 Your masterpiece has been created!</div>', unsafe_allow_html=True)
                        
                        st.rerun()
                    else:
                        progress_container.empty()
                        st.markdown('<div class="error-box">❌ No image was generated. Please try again with a different prompt.</div>', unsafe_allow_html=True)
                
                except Exception as e:
                    progress_container.empty()
                    
                    # Detailed error handling
                    error_msg = str(e).lower()
                    
                    if "api key" in error_msg or "authentication" in error_msg:
                        st.markdown('<div class="error-box">🔑 Authentication Error: Please check your API key configuration.</div>', unsafe_allow_html=True)
                    elif "quota" in error_msg or "limit" in error_msg:
                        st.markdown('<div class="error-box">⏳ Rate Limit: You\'ve reached the API limit. Please try again later.</div>', unsafe_allow_html=True)
                    elif "safety" in error_msg or "policy" in error_msg:
                        st.markdown('<div class="error-box">🛡️ Content Policy: Your prompt may violate content guidelines. Please try a different description.</div>', unsafe_allow_html=True)
                    elif "network" in error_msg or "connection" in error_msg:
                        st.markdown('<div class="error-box">🌐 Network Error: Please check your internet connection and try again.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-box">⚠️ Generation Error: {str(e)}</div>', unsafe_allow_html=True)
                    
                    # Troubleshooting tips
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        - **API Issues**: Verify your Gemini API key in secrets.toml
                        - **Content Policy**: Avoid prompts with violence, adult content, or copyrighted material
                        - **Rate Limits**: Wait a few minutes between requests
                        - **Network**: Check your internet connection
                        - **Prompt Issues**: Try simpler, more descriptive prompts
                        """)

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
    
    with st.expander("✨ Prompt Writing Guide", expanded=False):
        st.markdown("""
        **Structure your prompt:**
        1. **Subject**: What/who is the main focus?
        2. **Setting**: Where does it take place?
        3. **Style**: Art style or technique
        4. **Mood**: Atmosphere and emotion
        5. **Details**: Colors, lighting, composition
        
        **Example**: *"A mystical forest guardian, ancient oak setting, Studio Ghibli style, serene mood, soft golden lighting"*
        """)
        
    
    
    with st.expander("🎨 Style Examples"):
        st.markdown("""
        - **Photorealistic**: "Ultra-realistic, 8K, professional photography"
        - **Artistic**: "Oil painting, impressionist, brush strokes visible"
        - **Cinematic**: "Movie poster style, dramatic lighting, epic composition"
        - **Fantasy**: "Magic realism, ethereal glow, mythical atmosphere"
        """)

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

            # --- CORRECTED: CLEAR CHAT BUTTON LOGIC ---
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                # Only reset the chat history, keeping the image
                st.session_state.image_chat_history = []
                st.rerun() # Rerun to update the UI immediately

            # Display the chat history
            for message in st.session_state.image_chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

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
                    except Exception as e:
                        st.error(f"Color extraction failed: {e}")

        # Display the palette result if it exists
        if 'palette_result' in st.session_state and st.session_state.palette_result:
            st.markdown("---")
            st.markdown("#### ✨ Extracted Palette")
            
            hex_colors = st.session_state.palette_result
            cols = st.columns(len(hex_colors))
            for i, hex_color in enumerate(hex_colors):
                with cols[i]:
                    st.markdown(f'<div style="background-color: {hex_color}; height: 80px; width: 100%; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);"></div>', unsafe_allow_html=True)
                    st.code(hex_color, language=None)
            
            # --- START: ADDED DOWNLOAD OPTIONS ---
            st.markdown("---")
            st.markdown("##### 💾 Download Palette")
            
            dl_col1, dl_col2 = st.columns(2)

            # 1. Download as JSON
            with dl_col1:
                palette_json = json.dumps({"colors": hex_colors}, indent=2)
                st.download_button(
                    label="📄 Download JSON",
                    data=palette_json,
                    file_name=f"palette_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )

            # 2. Download as Image
            with dl_col2:
                # Create a palette image
                swatch_size = 100
                palette_img = Image.new('RGB', (len(hex_colors) * swatch_size, swatch_size))
                for i, color in enumerate(hex_colors):
                    color_swatch = Image.new('RGB', (swatch_size, swatch_size), color)
                    palette_img.paste(color_swatch, (i * swatch_size, 0))

                img_buffer = BytesIO()
                palette_img.save(img_buffer, format="PNG")
                
                st.download_button(
                    label="🖼️ Download Image",
                    data=img_buffer.getvalue(),
                    file_name=f"palette_{int(time.time())}.png",
                    mime="image/png",
                    use_container_width=True
                )
            # --- END: ADDED DOWNLOAD OPTIONS ---
    # --- END: COLOR PALETTE GENERATOR ---

    # --- START: IMAGE COLORIZER ---
    with st.expander("🎨 Image Colorizer", expanded=False):
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
                        
                        st.session_state.colorized_result_data = None
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                st.session_state.colorized_result_data = part.inline_data.data
                                break

                        if not st.session_state.colorized_result_data:
                            st.error("The model did not return a colorized image. Please try again.")

                    except Exception as e:
                        st.error(f"Colorization failed: {e}")

        # Display the colorized result if it exists
        if 'colorized_result_data' in st.session_state and st.session_state.colorized_result_data:
            st.markdown("---")
            st.markdown("#### ✨ Colorized Result")

            colorized_data = st.session_state.colorized_result_data
            result_img_colorized = Image.open(BytesIO(colorized_data))
            
            st.image(result_img_colorized, use_container_width=True, caption=f"Colorized Image ({result_img_colorized.size[0]}x{result_img_colorized.size[1]})")
            
            st.download_button(
                label="📥 Download Colorized Image",
                data=colorized_data,
                file_name=f"colorized_{colorizer_image.name}",
                mime="image/png",
                use_container_width=True
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
                        st.session_state.sketch_art_result = output_buffer.getvalue()

                    except Exception as e:
                        st.error(f"Sketch conversion failed: {e}")

        if 'sketch_art_result' in st.session_state and st.session_state.sketch_art_result:
            st.markdown("---")
            st.markdown("#### ✨ Sketch Result")
            result_sketch_data = st.session_state.sketch_art_result
            st.image(result_sketch_data, use_container_width=True, caption="Your generated sketch")
            st.download_button(
                label="💾 Download as .png file",
                data=result_sketch_data,
                file_name=f"sketch_art_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
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
                        st.session_state.glitch_art_result = output_buffer.getvalue()
                    except Exception as e:
                        st.error(f"Glitch effect failed: {e}")

        if 'glitch_art_result' in st.session_state and st.session_state.glitch_art_result:
            st.markdown("---")
            st.markdown("#### ✨ Glitch Art Result")
            result_glitch_data = st.session_state.glitch_art_result
            st.image(result_glitch_data, use_container_width=True, caption="Your glitched masterpiece")
            st.download_button(
                label="💾 Download as .png file",
                data=result_glitch_data,
                file_name=f"glitch_art_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
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
                        st.session_state.halftone_art_result = output_buffer.getvalue()
                    except Exception as e:
                        st.error(f"Halftone effect failed: {e}")

        if 'halftone_art_result' in st.session_state and st.session_state.halftone_art_result:
            st.markdown("---")
            st.markdown("#### ✨ Halftone Result")
            st.image(st.session_state.halftone_art_result, use_container_width=True, caption="Your generated halftone print")
            st.download_button(label="💾 Download as .png file", data=st.session_state.halftone_art_result, file_name=f"halftone_art_{int(time.time())}.png", mime="image/png", use_container_width=True)
    # --- END: HALFTONE PRINT EFFECT ---

    # --- START: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # This container is now outside the 'if' condition, so it appears on startup.
    # --- START: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # This container is now outside the 'if' condition, so it appears on startup.
    with st.container(border=True):
        st.markdown("##### ✨ Feeling Lucky?")

        def generate_random_prompt():
            # NOTE: This assumes 'random' is imported.
            
            # ==============================================================================
            # >>> EXPANDED SUBJECTS LIST (200+ items)
            # ==============================================================================
            subjects = [
                # Fantasy & Mythology
                "A majestic dragon soaring over a volcanic landscape",
                "An ancient tree spirit with glowing eyes",
                "A celestial fox with nine tails, leaping through stars",
                "A forgotten library in the clouds",
                "A knight in ethereal, glowing armor",
                "A city carved into a giant crystal",
                "A griffin nesting on a skyscraper",
                "The world turtle swimming through the cosmos",
                "A valkyrie descending from Valhalla",
                "A phoenix being reborn from ashes",
                "An enchanted forest where trees whisper secrets",
                "A floating castle held aloft by magic",
                "A mermaid queen on her coral throne",
                "A dwarven city deep within a mountain, lit by forge fires",
                "An elven archer with a bow made of moonlight",
                "A kraken attacking a fleet of galleons",
                "A wizard's tower filled with arcane artifacts",
                "A goblin marketplace bustling with strange creatures",
                "A druid communing with nature spirits",
                "The Gates of Olympus, guarded by a cerberus",
                "A kitsune in human form, walking through a Kyoto street",
                "A golem made of ancient stone and vines",
                "A dryad merging with her host tree",
                "A steampunk airship navigating a storm",
                "A leviathan sleeping in the abyssal deep",

                # Sci-Fi & Futuristic
                "A futuristic city skyline at sunset",
                "A robot gardener tending to glowing alien plants",
                "An alien marketplace on a distant planet",
                "A lone astronaut discovering an ancient alien artifact",
                "A bustling spaceport with ships from a thousand worlds",
                "A cyberpunk detective in a rain-soaked neon city",
                "A massive generation ship traveling between galaxies",
                "A cyborg samurai in a bamboo forest",
                "An abandoned terraforming colony on Mars",
                "A Dyson sphere under construction",
                "An android dreaming of electric sheep",
                "A mech battle in a ruined metropolis",
                "A glowing data stream inside a quantum computer",
                "A city floating in the rings of Saturn",
                "A portal to another dimension opening in a city square",
                "A bio-mechanical jungle on a newly discovered world",
                "A sleek starfighter in a cosmic dogfight",
                "The interior of a massive space station",
                "A post-apocalyptic scavenger with a cybernetic pet",
                "A hovercraft race through canyons",
                "An AI core room, visualized as a cathedral of light",
                "A soldier in high-tech powered armor",
                "A serene city on the moon, under a glass dome",
                "A wormhole bridge connecting two galaxies",
                "A hacker interfacing with a virtual world",

                # Historical & Real-World
                "A Roman legion marching through a dense forest",
                "A samurai warrior meditating under a cherry blossom tree",
                "A Viking longship sailing through a misty fjord",
                "A bustling marketplace on the ancient Silk Road",
                "The library of Alexandria in its prime",
                "A pharaoh's tomb being discovered in Egypt",
                "A medieval castle under siege",
                "A Parisian street cafe in the 1920s",
                "A Venetian carnival with elaborate masks",
                "A lone cowboy overlooking the Grand Canyon",
                "An Aztec temple at the height of the empire",
                "A gladiator fight in the Colosseum",
                "A quiet monastery in the Himalayas",
                "A 1950s American diner at midnight",
                "The construction of the Eiffel Tower",
                "A secret agent in Cold War Berlin",
                "A bustling Victorian London street",

                # Nature & Animals
                "A hidden waterfall oasis in a lush jungle",
                "A majestic lion with a crown of stars",
                "A pod of whales swimming through an aurora borealis",
                "A hummingbird frozen in time, its wings a rainbow blur",
                "A wise old elephant leading its herd",
                "A forest of giant, bioluminescent mushrooms",
                "A serene Japanese garden with a koi pond",
                "A powerful volcanic eruption at night",
                "A desert landscape under a galaxy-filled sky",
                "A red panda sleeping on a mossy branch",
                "A coral reef teeming with vibrant life",
                "A lone wolf howling at the full moon",
                "A majestic eagle catching a fish from a river",
                "A sea turtle gliding through sunlit ocean waters",
                "The Amazon rainforest, viewed from the canopy",
                "A polar bear on a shrinking ice floe",
                "A field of sunflowers turning towards the sun",

                # Surreal & Abstract
                "A clock melting over a branch, in the style of Dali",
                "A staircase that spirals into the clouds",
                "A city where the buildings are made of books",
                "A person made of constellations and stardust",
                "A forest where the trees are made of glass",
                "An ocean made of liquid galaxies",
                "A room where gravity is sideways",
                "A chess game played by shadows",
                "The sound of silence, visualized",
                "A teacup containing a storm",
                "A doorway to summer in the middle of a snowy field",
                "A train that travels through memories",
                "A bridge made of woven moonlight",
                "A human heart made of clockwork and gears",
                "A desert filled with shipwrecks",
                "An orchestra of plants playing music",
                "A face emerging from a canyon wall",

                # People & Characters
                "An old watchmaker in his workshop, surrounded by timepieces",
                "A street artist painting a mural on a brick wall",
                "A child reading a book under a magical, glowing tree",
                "A chef in a chaotic, fantastical kitchen",
                "A musician playing a violin that summons spirits",
                "A scholar deciphering an ancient, glowing scroll",
                "A deep-sea diver discovering an underwater city",
                "A queen addressing her court in a grand throne room",
                "A lonely lighthouse keeper during a storm",
                "A ballerina whose dance creates ripples in reality",
                "A blacksmith forging a legendary sword",
                "A nomad traveling with a giant, gentle beast",
                "A plague doctor in a deserted, gothic city",
                "A pilot of a fantastical flying machine",
                "A spy attending a masquerade ball",
            ]
            
            # ==============================================================================
            # >>> EXPANDED DETAILS LIST (200+ items)
            # ==============================================================================
            details = [
                # Artistic Styles
                "in the style of a classical oil painting",
                "as a vibrant watercolor illustration",
                "in the style of Hayao Miyazaki",
                "in the style of a detailed charcoal sketch",
                "with an impressionist art style, visible brush strokes",
                "in a surrealist style, like Salvador Dalí",
                "with a pop art aesthetic, like Andy Warhol",
                "as a vintage Japanese ukiyo-e woodblock print",
                "in a modern anime or manga style",
                "in the style of a gritty comic book panel",
                "as a beautiful stained glass window",
                "in the distinct style of Vincent van Gogh",
                "with an art nouveau decorative style",
                "in a minimalist, clean vector art style",
                "as a pointillism painting",
                "in a cubist style, like Picasso",
                "as a piece of high-fantasy concept art",
                "in the style of Moebius (Jean Giraud)",
                "as a psychedelic, trippy art piece",
                "in the style of a children's storybook illustration",
                "with a dark, gothic art style",
                "in the style of classic Disney animation",
                "as a photobashed, realistic concept piece",
                "in an abstract expressionist style",
                "as a medieval illuminated manuscript",
                "with a street art graffiti aesthetic",
                "in the style of H.R. Giger, biomechanical",

                # Lighting & Color
                "with dramatic, cinematic lighting",
                "with an ethereal, otherworldly glow",
                "in vibrant, rich, saturated colors",
                "with a soft, dreamy, and gentle focus",
                "bathed in the golden hour light of sunset",
                "illuminated by a neon, cyberpunk glow",
                "in a stark black and white, high contrast",
                "with a monochromatic color scheme",
                "with a pastel color palette",
                "lit by magical, bioluminescent light sources",
                "with volumetric lighting and god rays streaming down",
                "using a chiaroscuro lighting technique",
                "with a warm and cozy, candlelit atmosphere",
                "in a cool, moody blue and purple color palette",
                "with a nostalgic sepia tone",
                "backlit, creating a powerful silhouette",
                "with shimmering, iridescent colors",
                "with a vaporwave aesthetic, pinks and cyans",
                "in a dark, foreboding, and ominous light",
                "lit by the light of a full moon",
                "with lens flare and anamorphic streaks",

                # Composition & Framing
                "as an ultra-wide, panoramic shot",
                "in a detailed macro, close-up view",
                "shot with a fisheye lens",
                "from a dramatic low-angle perspective",
                "viewed from a bird's-eye-view, looking down",
                "with a symmetrical and balanced composition",
                "using the rule of thirds for a dynamic composition",
                "with a shallow depth of field, beautiful bokeh",
                "in a cinematic widescreen aspect ratio",

                # Mood & Atmosphere
                "exuding a sense of wonder and awe",
                "with a dramatic and epic atmosphere",
                "filled with intricate, fractal patterns",
                "creating a feeling of peace and tranquility",
                "with a mysterious and enigmatic mood",
                "conveying a sense of profound loneliness",
                "in a whimsical and playful setting",
                "with a dark, dystopian, and oppressive feeling",
                "creating a sense of grand scale and adventure",
                "with a cozy, comfortable, and safe atmosphere",
                "in a chaotic and energetic scene",
                "with a nostalgic and melancholic tone",
                "exuding power and majesty",
                "in a serene and meditative environment",

                # Rendering & Texture
                "rendered in Unreal Engine 5, hyperrealistic",
                "as a hyper-detailed, 8K resolution photograph",
                "with a glossy, reflective finish",
                "with a rough, textured, matte finish",
                "made of polished chrome and glass",
                "appearing weathered, ancient, and worn",
                "with a grainy, film-like texture",
                "in sharp, crisp focus from front to back",
                "with heavy impasto, thick paint strokes",
                "made of translucent, glowing crystal",
                "etched in gold and silver",
                "with a cel-shaded, cartoon-like rendering",
                "as an intricate line art drawing",
                "with a smooth, airbrushed quality",
                "rendered in Octane, cinematic VFX",
            ]

            # Combine the parts into a full prompt
            full_prompt = f"{random.choice(subjects)}, {random.choice(details)}"
            
            # Apply the generated prompt to the main text area in your app
            st.session_state.main_prompt = full_prompt

        st.button(
            "🎲 Surprise Me!", 
            on_click=generate_random_prompt, 
            use_container_width=True,
            help="Generate a random, creative prompt to get you started."
        )
    # --- END: SURPRISE ME - RANDOM PROMPT GENERATOR ---
    # --- END: SURPRISE ME - RANDOM PROMPT GENERATOR ---


    # Quick actions will still only appear after the first image is generated.
    if st.session_state.images:
        st.markdown("### 🦄 Quick Actions")


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
                    for prompt in display_list:
                        with st.container(border=True):
                            st.markdown(f"<small>{prompt[:100]}...</small>", unsafe_allow_html=True)
                            # Use a hash of the prompt for a unique, stable key
                            st.button(
                                "✍️ Use This Prompt", 
                                key=f"hist_use_{hash(prompt)}", 
                                on_click=apply_historical_prompt, 
                                args=(prompt,), 
                                use_container_width=True
                            )
                
                st.markdown("---")
                if st.button("Clear Entire History", use_container_width=True):
                    st.session_state.prompt_history = []
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
                    cols = st.columns(3)
                    for i, fav_img_data in enumerate(display_list):
                        with cols[i % 3]:
                            thumb = Image.open(BytesIO(fav_img_data['image_data']))
                            thumb.thumbnail((150, 150))
                            
                            # Use the unique image ID for the key to prevent errors
                            if st.button(f"{i+1}", key=f"fav_view_{fav_img_data['id']}", use_container_width=True):
                                st.session_state.current_image = fav_img_data
                                st.rerun()
                            st.image(thumb, use_container_width=True)

                st.markdown("---")
                if st.button("🗑️ Clear All Favorites", use_container_width=True, key="clear_favorites"):
                    st.session_state.favorites = []
                    save_favorites_to_db()
                    st.rerun()



        
        
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

st.sidebar.image("k15.jpg", use_container_width=True)


# Select one image at random from the list


# Display the randomly selected image
st.image("k19.jpg", use_container_width=True)

# --- END: RANDOM GALLERY IMAGE DISPLAY ---


st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
    <p>✨ Powered by Google Gemini Flash • Created with ❤️ for artists and dreamers</p>
    <p style="font-size: 0.8rem;">Transform your imagination into reality with AI-powered artistry</p>
</div>
""", unsafe_allow_html=True)
