import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import json
from gtts import gTTS
import time
import random
import uuid

# Page config
st.set_page_config(
    page_title="🖼️ DreamCanvas",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)



st.sidebar.image("k5.jpg", use_container_width=True)



# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
# ... after initializing 'current_image'
if 'prompt_history' not in st.session_state:
    st.session_state.prompt_history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    :root {
        /* Cosmic Color Palette - Easy on Eyes */
        --void-black: #0a0a0f;
        --deep-space: #12121a;
        --nebula-dark: #1a1a27;
        --stardust-gray: #262634;
        --cosmic-mist: #3a3a4a;
        
        /* Soft Accent Colors */
        --dream-purple: #7c3aed;
        --cosmic-blue: #3b82f6;
        --nebula-cyan: #22d3ee;
        --aurora-green: #10b981;
        --stellar-pink: #f472b6;
        --moon-white: #f8fafc;
        
        /* Text Colors - Gentle on Eyes */
        --text-primary: #e2e8f0;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --text-dim: #64748b;
        
        /* Glow Effects */
        --soft-glow: rgba(124, 58, 237, 0.15);
        --gentle-glow: rgba(59, 130, 246, 0.1);
        --dream-glow: rgba(34, 211, 238, 0.08);
    }
    
    /* Main App Background */
    .stApp {
        background: 
            radial-gradient(ellipse 80% 50% at 50% -20%, var(--nebula-dark) 0%, transparent 70%),
            radial-gradient(ellipse 60% 80% at 90% 120%, rgba(124, 58, 237, 0.05) 0%, transparent 70%),
            linear-gradient(180deg, var(--deep-space) 0%, var(--void-black) 100%);
        background-attachment: fixed;
        color: var(--text-primary);
        min-height: 100vh;
        position: relative;
    }
    
    /* Subtle Floating Stars Effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(1px 1px at 25px 35px, rgba(248, 250, 252, 0.3), transparent),
            radial-gradient(1px 1px at 85px 75px, rgba(124, 58, 237, 0.4), transparent),
            radial-gradient(1px 1px at 145px 125px, rgba(34, 211, 238, 0.3), transparent),
            radial-gradient(1px 1px at 205px 45px, rgba(248, 250, 252, 0.2), transparent),
            radial-gradient(1px 1px at 275px 185px, rgba(59, 130, 246, 0.3), transparent),
            radial-gradient(1px 1px at 325px 95px, rgba(244, 114, 182, 0.2), transparent);
        background-repeat: repeat;
        background-size: 350px 200px;
        animation: gentleFloat 25s linear infinite;
        pointer-events: none;
        z-index: -1;
        opacity: 0.7;
    }
    
    @keyframes gentleFloat {
        0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.7; }
        25% { transform: translateY(-10px) translateX(5px); opacity: 0.5; }
        50% { transform: translateY(-5px) translateX(-3px); opacity: 0.8; }
        75% { transform: translateY(-15px) translateX(8px); opacity: 0.4; }
    }
    
    /* DreamCanvas Title Container */
    .title-container {
        background: 
            linear-gradient(135deg, 
                rgba(124, 58, 237, 0.08) 0%,
                rgba(59, 130, 246, 0.05) 35%,
                rgba(34, 211, 238, 0.08) 70%,
                rgba(16, 185, 129, 0.06) 100%
            );
        backdrop-filter: blur(20px);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin: 2rem auto;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(248, 250, 252, 0.05);
    }
    
    /* Subtle Rotating Border Effect */
    .title-container::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: conic-gradient(
            from 0deg,
            transparent 0deg,
            rgba(124, 58, 237, 0.2) 90deg,
            transparent 180deg,
            rgba(34, 211, 238, 0.15) 270deg,
            transparent 360deg
        );
        border-radius: 22px;
        animation: slowRotate 30s linear infinite;
        z-index: -1;
        opacity: 0.6;
    }
    
    @keyframes slowRotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* DreamCanvas Title Text */
    .dream-title {
        font-size: clamp(2.5rem, 5vw, 3.8rem);
        font-weight: 800;
        background: linear-gradient(
            135deg,
            #f8fafc 0%,
            #e0e7ff 20%,
            #c7d2fe 40%,
            #a5b4fc 60%,
            #8b5cf6 80%,
            #7c3aed 100%
        );
        background-size: 200% 200%;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: dreamShimmer 6s ease-in-out infinite;
        margin: 0;
        letter-spacing: -0.02em;
        position: relative;
    }
    
    @keyframes dreamShimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Subtitle */
    .dream-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
        margin-top: 0.75rem;
        font-weight: 400;
        opacity: 0.8;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
    
    /* Buttons with Soft Glass Effect */
    .stButton > button {
        background: linear-gradient(
            135deg,
            rgba(124, 58, 237, 0.12) 0%,
            rgba(59, 130, 246, 0.08) 100%
        );
        backdrop-filter: blur(12px);
        border: 1px solid rgba(124, 58, 237, 0.2);
        color: var(--text-primary);
        padding: 0.8rem 1.8rem;
        border-radius: 12px;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(248, 250, 252, 0.05);
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
            rgba(248, 250, 252, 0.08) 50%,
            transparent 100%
        );
        transition: left 0.4s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 
            0 8px 24px rgba(124, 58, 237, 0.15),
            inset 0 1px 0 rgba(248, 250, 252, 0.1);
        border-color: rgba(124, 58, 237, 0.3);
        background: linear-gradient(
            135deg,
            rgba(124, 58, 237, 0.18) 0%,
            rgba(59, 130, 246, 0.12) 100%
        );
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Sidebar - Deep Space */
    .stSidebar {
        background: linear-gradient(
            180deg,
            rgba(26, 26, 39, 0.95) 0%,
            rgba(18, 18, 26, 0.98) 100%
        );
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(124, 58, 237, 0.1);
    }
    
    .stSidebar > div {
        background: transparent;
    }
    
    /* Input Fields - Soft and Easy on Eyes */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(124, 58, 237, 0.04) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(148, 163, 184, 0.15) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 0.9rem !important;
        font-size: 0.95rem;
        transition: all 0.25s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(124, 58, 237, 0.3) !important;
        box-shadow: 
            0 0 0 2px rgba(124, 58, 237, 0.1),
            0 4px 16px rgba(0, 0, 0, 0.12) !important;
        outline: none !important;
        background: rgba(124, 58, 237, 0.06) !important;
    }
    
    /* Select Boxes */
    .stSelectbox > div > div {
        background: rgba(124, 58, 237, 0.04) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(148, 163, 184, 0.15) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
        padding: 0.7rem !important;
    }
    
    /* Headers with Gentle Gradients */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    
    .stMarkdown h3 {
        font-size: 1.4rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, var(--dream-purple), var(--nebula-cyan));
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        opacity: 0.9;
    }
    
    /* Expandable Sections */
    .stExpander > div > div > div > div {
        background: rgba(124, 58, 237, 0.04) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(148, 163, 184, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }
    
    /* Custom Containers */
    .cosmic-container {
        background: linear-gradient(
            135deg,
            rgba(16, 185, 129, 0.06) 0%,
            rgba(34, 211, 238, 0.08) 100%
        );
        backdrop-filter: blur(12px);
        border: 1px solid rgba(34, 211, 238, 0.15);
        padding: 1.5rem;
        border-radius: 16px;
        margin-top: 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    
    .dream-gallery {
        background: rgba(124, 58, 237, 0.04);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(148, 163, 184, 0.1);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }
    
    .gallery-item {
        background: rgba(248, 250, 252, 0.03);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(148, 163, 184, 0.08);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.75rem 0;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .gallery-item:hover {
        background: rgba(124, 58, 237, 0.08);
        border-color: rgba(124, 58, 237, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.1);
    }
    
    .gallery-item.selected {
        background: rgba(124, 58, 237, 0.1);
        border-color: rgba(124, 58, 237, 0.25);
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.15);
    }
    
    /* Status Messages */
    .error-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.08));
        backdrop-filter: blur(8px);
        border: 1px solid rgba(239, 68, 68, 0.2);
        padding: 1rem;
        border-radius: 12px;
        color: #fca5a5;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.1);
    }
    
    .success-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.08));
        backdrop-filter: blur(8px);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 1rem;
        border-radius: 12px;
        color: #86efac;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1);
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(124, 58, 237, 0.08));
        backdrop-filter: blur(8px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        padding: 1rem;
        border-radius: 12px;
        color: #bfdbfe;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(34, 211, 238, 0.12)) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        color: var(--text-primary) !important;
        padding: 0.7rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1);
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(34, 211, 238, 0.18)) !important;
        border-color: rgba(16, 185, 129, 0.35) !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.15);
    }
    
    /* Smooth Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(148, 163, 184, 0.05);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(124, 58, 237, 0.2);
        border-radius: 3px;
        transition: all 0.25s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(124, 58, 237, 0.35);
    }
    
    /* Gentle Loading Animation */
    @keyframes gentlePulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.7; }
    }
    
    .loading-pulse {
        animation: gentlePulse 2.5s ease-in-out infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .title-container {
            padding: 2rem 1.5rem;
            margin: 1rem;
        }
        
        .dream-title {
            font-size: 2.2rem;
        }
        
        .dream-subtitle {
            font-size: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# DreamCanvas Title
st.markdown("""
<div class="title-container">
    <h1 class="dream-title">DreamCanvas</h1>
    <p class="dream-subtitle">Text to Image • Painting Possibilities</p>
</div>
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
        st.markdown("### 🖼️ Your Gallery")
        
        # Clear gallery button
        if st.button("🗑️ Clear Gallery", use_container_width=True):
            st.session_state.images = []
            st.session_state.current_image = None
            st.rerun()
        
        # Display thumbnail gallery
        for i, img_data in enumerate(st.session_state.images):
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    # Create thumbnail
                    img = Image.open(BytesIO(img_data['image_data']))
                    img.thumbnail((80, 80))
                    st.image(img, use_container_width=True)
                
                with col2:
                    if st.button(f"{i+1}", key=f"view_{i}", use_container_width=True):
                        st.session_state.current_image = img_data
                        st.rerun()
                        
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
    
    # Prompt enhancement options
    enhance_prompt = st.checkbox("🚀 Auto-enhance prompt with selected styles", key="enhance_check")
    
    # Generate button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        if st.button("✨ Generate Masterpiece", key="generate_btn", use_container_width=True):
            if not prompt.strip():
                st.markdown('<div class="error-box">❌ Please enter a prompt to begin your creative journey!</div>', unsafe_allow_html=True)
            else:
                # Clear any previously displayed variations for a clean slate
                if 'newly_generated_variations' in st.session_state:
                    st.session_state.newly_generated_variations = None
                
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
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp-image-generation",
                        contents=enhanced_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["text", "image"]
                        )
                    )
                    # ... The rest of your try...except block continues from here ...
                    
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
            else:
                st.session_state.favorites.append(image_id)

        # Use a filled or empty star for visual feedback
        is_favorited = img_data['id'] in st.session_state.favorites
        star_icon = "★" if is_favorited else "☆"
        
        st.button(
            f"{star_icon} {'Favorited' if is_favorited else 'Favorite'}", 
            on_click=toggle_favorite, 
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

                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=[variation_prompt, original_image_pil],
                            config=types.GenerateContentConfig(
                                response_modalities=["text", "image"]
                            )
                        )

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
                on_click=toggle_favorite_variation, 
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
            st.markdown("### 💾 Export Your Variation Masterpiece")
            
            # Open the image data once for reuse
            variation_img = Image.open(BytesIO(variation_data['image_data']))
            
            # Create two columns for the buttons
            dl_col1, dl_col2 = st.columns(2)

            with dl_col1:
                # PNG download logic
                png_buffer = BytesIO()
                variation_img.save(png_buffer, format="PNG", optimize=True)
                st.download_button(
                    label="📥 Download PNG",
                    data=png_buffer.getvalue(),
                    file_name=f"variation_{int(time.time())}.png",
                    mime="image/png",
                    key=f"dl_var_png_{variation_data['id']}",
                    use_container_width=True
                )

            with dl_col2:
                # JPG download logic
                jpg_buffer = BytesIO()
                # Handle transparency for JPG conversion
                if variation_img.mode == 'RGBA':
                    jpg_img = Image.new('RGB', variation_img.size, (255, 255, 255))
                    jpg_img.paste(variation_img, mask=variation_img.split()[-1])
                else:
                    jpg_img = variation_img
                jpg_img.save(jpg_buffer, format="JPEG", quality=95, optimize=True)
                st.download_button(
                    label="📥 Download JPG",
                    data=jpg_buffer.getvalue(),
                    file_name=f"variation_{int(time.time())}.jpg",
                    mime="image/jpeg",
                    key=f"dl_var_jpg_{variation_data['id']}",
                    use_container_width=True
                )
            # --- END: EXPORT BUTTONS FOR VARIATION ---

            if st.button("Clear Variation Display", use_container_width=True):
                 st.session_state.newly_generated_variations = None
                 st.rerun()

            
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
        # --- END: DISPLAY NEW VARIATION ---

            


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
    
    # Quick actions
    if st.session_state.images:
        st.markdown("### 🦄 Quick Actions")


        # --- START: PROMPT HISTORY & FAVORITES FEATURE ---

        # 1. Prompt History
        with st.expander("📜 Prompt History"):
            if not st.session_state.prompt_history:
                st.info("Your recent prompts will appear here.")
            else:
                def apply_historical_prompt(prompt_text):
                    st.session_state.main_prompt = prompt_text
                
                for i, prompt in enumerate(st.session_state.prompt_history[:10]): # Show last 10
                    with st.container(border=True):
                        st.markdown(f"<small>{prompt[:100]}...</small>", unsafe_allow_html=True)
                        st.button("✍️ Use", key=f"hist_{i}", on_click=apply_historical_prompt, args=(prompt,), use_container_width=True)
                
                if st.button("Clear History", use_container_width=True):
                    st.session_state.prompt_history = []
                    st.rerun()

        # 2. Favorites
        with st.expander("⭐ Favorites"):
            if not st.session_state.favorites:
                st.info("Your favorite images will appear here. Click the ☆ icon on an image to save it.")
            else:
                favorited_images = [img for img in st.session_state.images if img['id'] in st.session_state.favorites]
                
                # Create a grid for thumbnails
                cols = st.columns(3)
                for i, fav_img_data in enumerate(favorited_images):
                    with cols[i % 3]:
                        thumb = Image.open(BytesIO(fav_img_data['image_data']))
                        thumb.thumbnail((100, 100))
                        
                        if st.button(f"{i+1}", key=f"fav_btn_{i}", use_container_width=True):
                            st.session_state.current_image = fav_img_data
                            st.rerun()
                        st.image(thumb, use_container_width=True)

        # --- END: PROMPT HISTORY & FAVORITES FEATURE ---



        
        
        if st.button("🎲 Random Style", use_container_width=True):
            import random
            random_category = random.choice(list(STYLE_CATEGORIES.keys()))
            random_style = random.choice(STYLE_CATEGORIES[random_category])
            st.session_state.temp_style = f"{random_category}: {random_style}"
            st.rerun()


        # --- START: SURPRISE ME - RANDOM PROMPT GENERATOR ---
        with st.container(border=True):
            st.markdown("##### ✨ Feeling Lucky?")

            def generate_random_prompt():
                # Define components for building a creative prompt
                subjects = [
                    "A majestic dragon", "A futuristic city skyline", "A hidden waterfall oasis", 
                    "An ancient tree spirit", "A celestial fox", "A forgotten library in the clouds", 
                    "A steampunk airship navigating a storm", "A robot gardener tending to glowing plants", 
                    "A knight in ethereal armor", "An alien marketplace"
                ]
                details = [
                    "with cinematic lighting", "with an ethereal glow", "in vibrant, rich colors",
                    "exuding a sense of wonder", "with a dramatic atmosphere", "filled with intricate patterns",
                    "rendered in Unreal Engine 5", "in a hyperrealistic style", "as a piece of concept art",
                    "with a soft, dreamy focus"
                ]
                
                # Select a random style from your existing categories
                random_category = random.choice(list(STYLE_CATEGORIES.keys()))
                random_style = random.choice(STYLE_CATEGORIES[random_category])

                # Combine the parts into a full prompt
                full_prompt = f"{random.choice(subjects)}, in the style of {random_style}, {random.choice(details)}"
                
                # Apply the generated prompt to the main text area
                st.session_state.main_prompt = full_prompt

            st.button(
                "🎲 Surprise Me!", 
                on_click=generate_random_prompt, 
                use_container_width=True,
                help="Generate a random, creative prompt to get you started."
            )
        # --- END: SURPRISE ME - RANDOM PROMPT GENERATOR ---
        
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
gallery_images = [
    "k3.jpg", "k2.jpg", "k6.jpg", "k7.jpg", "k19.jpg", "k8.jpg", 
    "k4.jpg", "k16.jpg", "k13.jpg", "k14.jpg", "k17.jpg", "k1.jpg","k10.jpg","k9.jpg","k12.jpg","k18.jpg",
]

st.sidebar.image("k15.jpg", use_container_width=True)


# Select one image at random from the list
random_image_to_display = random.choice(gallery_images)

# Display the randomly selected image
st.image(random_image_to_display, use_container_width=True)

# --- END: RANDOM GALLERY IMAGE DISPLAY ---


st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
    <p>✨ Powered by Google Gemini Flash • Created with ❤️ for artists and dreamers</p>
    <p style="font-size: 0.8rem;">Transform your imagination into reality with AI-powered artistry</p>
</div>
""", unsafe_allow_html=True)
