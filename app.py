import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import json
import time
import uuid

# Page config
st.set_page_config(
    page_title="🖼️  Studio",
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
    
    # Mood presets - INSERT THIS SECTION HERE
    mood_preset = st.selectbox("🌙 Mood Presets", [
        "Custom", "Dreamy", "Ethereal", "Mystical", "Serene", 
        "Nostalgic", "Romantic", "Melancholic", "Whimsical", "Surreal"
    ])
    

# --- Expanded Mood Preset Configurations ---
# This dictionary contains over 200 detailed presets for generating creative visuals.
# Each preset includes suggested art styles, color moods, lighting conditions, and specific enhancements.

MOOD_PRESETS = {
    # --- Ethereal & Mystical ---
    "Dreamy": {
        "styles": ["Dream Imagery", "Sfumato", "Impressionism"],
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
        "color_mood": "Deep Jewels",
        "lighting": "Golden hour",
        "enhancement": "magical aura, ancient symbols, mystical energy, enchanted glow"
    },
    "Surreal": {
        "styles": ["Surrealism", "Dream Imagery", "Metaphysical Art"],
        "color_mood": "Vibrant",
        "lighting": "Dramatic",
        "enhancement": "impossible geometry, floating objects, dream logic, melting forms"
    },
    "Whimsical": {
        "styles": ["Children's Book Illustration", "Naive Art", "Folk Art"],
        "color_mood": "Vibrant",
        "lighting": "Natural",
        "enhancement": "playful characters, impossible physics, childlike wonder, charming details"
    },
    "Magical": {
        "styles": ["Magic Realism", "Fantasy", "Enchanted"],
        "color_mood": "Iridescent",
        "lighting": "Golden hour",
        "enhancement": "sparkles, magical auras, impossible wonders, shimmering particles"
    },
    "Enchanted": {
        "styles": ["Fairy Tale", "Magic Realism", "Romanticism"],
        "color_mood": "Pastel",
        "lighting": "Twilight",
        "enhancement": "fairy tale atmosphere, magical transformation, glowing flora"
    },
    "Fairytale": {
        "styles": ["Fairy Tale", "Children's Book", "Whimsical"],
        "color_mood": "Storybook Pastels",
        "lighting": "Soft",
        "enhancement": "storybook characters, magical kingdoms, happy endings, talking animals"
    },
    "Cosmic": {
        "styles": ["Space Art", "Nebula Painting", "Abstract"],
        "color_mood": "Cosmic Blues & Purples",
        "lighting": "Starlight",
        "enhancement": "galaxies, nebulae, constellations, celestial bodies, cosmic dust"
    },
    "Quantum": {
        "styles": ["Abstract", "Generative Art", "Fractal Art"],
        "color_mood": "Digital Neon",
        "lighting": "Pulsing",
        "enhancement": "subatomic particles, energy fields, probability clouds, interconnected webs"
    },

    # --- Dark & Foreboding ---
    "Dark": {
        "styles": ["Gothic", "Dark Fantasy", "Noir"],
        "color_mood": "Monochrome",
        "lighting": "Low Key",
        "enhancement": "deep shadows, darkness, mysterious atmosphere, foreboding mood"
    },
    "Gothic": {
        "styles": ["Gothic Art", "Medieval", "Romanticism"],
        "color_mood": "Monochrome with Red Accent",
        "lighting": "Candlelight",
        "enhancement": "cathedral architecture, gargoyles, stained glass, dramatic arches"
    },
    "Horror": {
        "styles": ["Horror", "Body Horror", "Gothic"],
        "color_mood": "Desaturated Reds",
        "lighting": "Harsh",
        "enhancement": "terrifying, nightmarish, grotesque, unsettling atmosphere, jump scares"
    },
    "Creepy": {
        "styles": ["Horror", "Surrealism", "Found Footage"],
        "color_mood": "Sickly Greens",
        "lighting": "Flickering",
        "enhancement": "uncanny valley, disturbing details, eerie silence, things that are 'off'"
    },
    "Spooky": {
        "styles": ["Gothic", "Halloween", "Dark Fantasy"],
        "color_mood": "High contrast Orange & Black",
        "lighting": "Moonlight",
        "enhancement": "haunted house, ghosts, cobwebs, spooky atmosphere, jack-o-lanterns"
    },
    "Eerie": {
        "styles": ["Surrealism", "Liminal Space", "Film Noir"],
        "color_mood": "Cool tones",
        "lighting": "Foggy",
        "enhancement": "unsettling calm, empty spaces, strange silence, liminal feeling"
    },
    "Haunting": {
        "styles": ["Gothic", "Romanticism", "Symbolism"],
        "color_mood": "Monochrome",
        "lighting": "Blue hour",
        "enhancement": "ghost stories, abandoned places, melancholic beauty, lingering spirits"
    },
    "Dystopian": {
        "styles": ["Cyberpunk", "Brutalism", "Industrial"],
        "color_mood": "Gritty & Muted",
        "lighting": "Harsh Neon",
        "enhancement": "oppressive government, environmental disaster, loss of individuality"
    },
    "Apocalyptic": {
        "styles": ["Post-Apocalyptic", "Wasteland", "Survivalist"],
        "color_mood": "Dusty & Burnt",
        "lighting": "Overcast",
        "enhancement": "ruined cities, overgrown nature, survival gear, desolate landscapes"
    },
    "Chaotic": {
        "styles": ["Abstract Expressionism", "Glitch Art", "Dadaism"],
        "color_mood": "Clashing Colors",
        "lighting": "Strobe",
        "enhancement": "chaotic energy, random patterns, spontaneous creation, visual noise"
    },

    # --- Calm & Serene ---
    "Serene": {
        "styles": ["Japanese Minimalism", "Sumi-e", "Impressionism"],
        "color_mood": "Natural",
        "lighting": "Morning Light",
        "enhancement": "peaceful, calm waters, gentle breeze, tranquil setting, sense of stillness"
    },
    "Peaceful": {
        "styles": ["Impressionism", "Landscape Photography", "Zen"],
        "color_mood": "Soft Greens & Blues",
        "lighting": "Soft",
        "enhancement": "harmony, balance, gentle movements, inner peace, quiet contemplation"
    },
    "Tranquil": {
        "styles": ["Japanese Minimalism", "Zen", "Watercolor"],
        "color_mood": "Cool tones",
        "lighting": "Natural",
        "enhancement": "still water, meditation, quiet moments, absolute serenity"
    },
    "Calm": {
        "styles": ["Minimalism", "Zen", "Pastoral"],
        "color_mood": "Pastel",
        "lighting": "Soft",
        "enhancement": "gentle breeze, calm seas, peaceful meadows, soothing repetition"
    },
    "Relaxing": {
        "styles": ["Impressionism", "Pastoral", "Zen"],
        "color_mood": "Warm tones",
        "lighting": "Golden hour",
        "enhancement": "comfortable spaces, soft textures, soothing colors, cozy nooks"
    },
    "Soothing": {
        "styles": ["Watercolor", "Pastel", "Soft Focus"],
        "color_mood": "Muted Pastels",
        "lighting": "Diffused",
        "enhancement": "gentle gradients, soft edges, comforting warmth, healing light"
    },
    "Zen": {
        "styles": ["Japanese Minimalism", "Sumi-e", "Enso"],
        "color_mood": "Monochrome",
        "lighting": "Natural",
        "enhancement": "simplicity, balance, mindfulness, empty space (Ma), rock gardens"
    },
    "Meditative": {
        "styles": ["Mandala", "Sacred Geometry", "Abstract"],
        "color_mood": "Earthy Tones",
        "lighting": "Natural",
        "enhancement": "sacred patterns, inner reflection, spiritual journey, hypnotic repetition"
    },
    "Spiritual": {
        "styles": ["Sacred Geometry", "Mandala", "Visionary Art"],
        "color_mood": "Gold & White",
        "lighting": "Divine Light",
        "enhancement": "divine light, sacred symbols, transcendent experience, aura"
    },
    "Harmony": {
        "styles": ["Harmonious", "Unified", "Peaceful"],
        "color_mood": "Analogous Colors",
        "lighting": "Soft",
        "enhancement": "perfect harmony, unified composition, peaceful unity, visual balance"
    },

    # --- Sentimental & Emotional ---
    "Nostalgic": {
        "styles": ["Vintage Photography", "Sepia", "Retro"],
        "color_mood": "Faded Vintage",
        "lighting": "Golden hour",
        "enhancement": "faded memories, old photographs, film grain, light leaks, sepia tones"
    },
    "Romantic": {
        "styles": ["Rococo", "Impressionism", "Art Nouveau"],
        "color_mood": "Rose & Gold",
        "lighting": "Candlelight",
        "enhancement": "soft roses, gentle breeze, romantic sunset, tender moments, lace"
    },
    "Melancholic": {
        "styles": ["Romanticism", "Symbolism", "Blue Period"],
        "color_mood": "Cool tones",
        "lighting": "Rainy Day",
        "enhancement": "solitude, rain on windowpane, autumn leaves, bittersweet emotions"
    },
    "Sad": {
        "styles": ["Melancholic", "Blue Period", "Sorrowful"],
        "color_mood": "Desaturated Blues",
        "lighting": "Blue hour",
        "enhancement": "deep sadness, sorrowful mood, tears, melancholic beauty, heartbreak"
    },
    "Lonely": {
        "styles": ["Solitude", "Isolated", "Melancholic"],
        "color_mood": "Cool Grays",
        "lighting": "Single Light Source",
        "enhancement": "profound loneliness, solitary figure, vast empty spaces, isolation"
    },
    "Hopeful": {
        "styles": ["Impressionism", "Luminism", "Contemporary"],
        "color_mood": "Sunrise Pinks & Oranges",
        "lighting": "Sunrise",
        "enhancement": "first light, new beginnings, looking towards the horizon, sense of optimism"
    },
    "Joyful": {
        "styles": ["Pop Art", "Fauvism", "Celebration"],
        "color_mood": "Bright & Vibrant",
        "lighting": "Sunny Day",
        "enhancement": "overflowing joy, radiant happiness, celebration, laughter, confetti"
    },
    "Happy": {
        "styles": ["Happy", "Cheerful", "Bright"],
        "color_mood": "Sunny Yellows",
        "lighting": "Natural",
        "enhancement": "genuine happiness, cheerful disposition, bright smile, sun-drenched scenes"
    },
    "Triumphant": {
        "styles": ["Heroic Realism", "Epic", "Monumental"],
        "color_mood": "Gold & Royal Blue",
        "lighting": "Spotlight",
        "enhancement": "victory pose, raising a flag, overcoming obstacles, heroic glory"
    },
    "Anxious": {
        "styles": ["Expressionism", "Surrealism", "Glitch Art"],
        "color_mood": "Jarring & Dissonant",
        "lighting": "Harsh & Unstable",
        "enhancement": "sense of dread, shaky lines, distorted reality, claustrophobia"
    },

    # --- Energetic & Dynamic ---
    "Energetic": {
        "styles": ["Abstract Expressionism", "Action Painting", "Futurism"],
        "color_mood": "Vibrant",
        "lighting": "Dynamic",
        "enhancement": "dynamic movement, explosive energy, kinetic force, motion lines"
    },
    "Dynamic": {
        "styles": ["Futurism", "Cubo-Futurism", "Motion Graphics"],
        "color_mood": "High contrast",
        "lighting": "Dramatic",
        "enhancement": "speed lines, motion blur, powerful forces, sense of velocity"
    },
    "Vibrant": {
        "styles": ["Pop Art", "Fauvism", "Street Art"],
        "color_mood": "Saturated & Vibrant",
        "lighting": "Bright",
        "enhancement": "saturated colors, bold contrasts, lively atmosphere, full of life"
    },
    "Bold": {
        "styles": ["Abstract Expressionism", "Pop Art", "Graffiti"],
        "color_mood": "High contrast",
        "lighting": "Dramatic",
        "enhancement": "strong statements, powerful imagery, confident strokes, unapologetic"
    },
    "Powerful": {
        "styles": ["Epic", "Heroic", "Monumental"],
        "color_mood": "High contrast",
        "lighting": "God Rays",
        "enhancement": "overwhelming scale, mighty forces, awe-inspiring presence, raw power"
    },
    "Intense": {
        "styles": ["Expressionism", "Baroque", "Dramatic"],
        "color_mood": "Deep Reds & Blacks",
        "lighting": "Harsh",
        "enhancement": "extreme emotions, raw energy, overwhelming presence, high tension"
    },
    "Dramatic": {
        "styles": ["Baroque", "Romanticism", "Chiaroscuro"],
        "color_mood": "High contrast",
        "lighting": "Dramatic",
        "enhancement": "theatrical lighting, emotional tension, grand gestures, heightened reality"
    },
    "Epic": {
        "styles": ["Historical Painting", "Heroic", "Cinematic"],
        "color_mood": "Cinematic",
        "lighting": "Dramatic",
        "enhancement": "legendary scale, heroic proportions, mythical grandeur, vast landscapes"
    },
    "Explosive": {
        "styles": ["Action Painting", "Abstract", "High-Speed Photography"],
        "color_mood": "Fiery Oranges & Yellows",
        "lighting": "Flash",
        "enhancement": "detonation, shrapnel, shockwaves, bursting energy, debris"
    },
    "Frenzied": {
        "styles": ["Action Painting", "Tachisme", "Abstract Expressionism"],
        "color_mood": "Chaotic Mix",
        "lighting": "Strobe",
        "enhancement": "frantic brushstrokes, chaotic movement, loss of control, high-speed action"
    },

    # --- Minimalist & Modern ---
    "Minimalist": {
        "styles": ["Minimalism", "Modern", "Clean"],
        "color_mood": "Monochrome",
        "lighting": "Natural",
        "enhancement": "clean lines, empty space, essential elements only, simplicity"
    },
    "Clean": {
        "styles": ["Modern", "Minimalist", "Scandinavian Design"],
        "color_mood": "White & Light Wood",
        "lighting": "Bright & Airy",
        "enhancement": "crisp edges, pure forms, uncluttered composition, immaculate"
    },
    "Simple": {
        "styles": ["Minimalism", "Zen", "Modern"],
        "color_mood": "Natural",
        "lighting": "Soft",
        "enhancement": "basic shapes, clear purpose, effortless beauty, fundamental forms"
    },
    "Modern": {
        "styles": ["Mid-Century Modern", "Bauhaus", "Contemporary"],
        "color_mood": "Neutral with a Pop of Color",
        "lighting": "Architectural",
        "enhancement": "sleek design, geometric forms, contemporary style, functional"
    },
    "Structured": {
        "styles": ["De Stijl", "Constructivism", "Geometric"],
        "color_mood": "Primary Colors",
        "lighting": "Flat",
        "enhancement": "organized composition, systematic arrangement, grid layout, architectural"
    },
    "Geometric": {
        "styles": ["Geometric Abstraction", "Cubism", "Suprematism"],
        "color_mood": "High contrast",
        "lighting": "Studio",
        "enhancement": "geometric shapes, mathematical precision, structured patterns, symmetry"
    },
    "Symmetrical": {
        "styles": ["Symmetrical", "Balanced", "Formalism"],
        "color_mood": "Natural",
        "lighting": "Even",
        "enhancement": "perfect symmetry, mirror images, balanced composition, classical order"
    },
    "Asymmetrical": {
        "styles": ["Asymmetrical", "Unbalanced", "Dynamic"],
        "color_mood": "Vibrant",
        "lighting": "Dramatic",
        "enhancement": "asymmetric composition, dynamic balance, visual tension, off-kilter"
    },
    "Balanced": {
        "styles": ["Balanced", "Harmonious", "Classical"],
        "color_mood": "Natural",
        "lighting": "Natural",
        "enhancement": "perfect balance, harmonious proportions, stability, visual equilibrium"
    },
    "Ordered": {
        "styles": ["Ordered", "Systematic", "Grid-based"],
        "color_mood": "Monochromatic",
        "lighting": "Flat",
        "enhancement": "perfect order, systematic arrangement, precise alignment, logical flow"
    },

    # --- Tech & Sci-Fi ---
    "Futuristic": {
        "styles": ["Cyberpunk", "Sci-Fi Concept Art", "Digital Art"],
        "color_mood": "Neon",
        "lighting": "Holographic",
        "enhancement": "advanced technology, holographic displays, sleek surfaces, flying vehicles"
    },
    "Cyberpunk": {
        "styles": ["Cyberpunk", "Neon Noir", "Biopunk"],
        "color_mood": "Neon Pinks & Blues",
        "lighting": "Neon",
        "enhancement": "neon lights, rain-soaked streets, high-tech low-life, cybernetics"
    },
    "Steampunk": {
        "styles": ["Steampunk", "Victorian Futurism", "Mechanical"],
        "color_mood": "Brass & Sepia",
        "lighting": "Gaslight",
        "enhancement": "brass gears, steam pipes, Victorian aesthetics, clockwork mechanisms"
    },
    "Technological": {
        "styles": ["Tech", "Digital", "Futuristic"],
        "color_mood": "Cool Blues & Silvers",
        "lighting": "LED",
        "enhancement": "circuits, data streams, technological interfaces, glowing lines"
    },
    "Digital": {
        "styles": ["Digital Art", "Pixel Art", "Glitch Art"],
        "color_mood": "RGB",
        "lighting": "Screen Glow",
        "enhancement": "pixels, digital artifacts, computer-generated imagery, glitches"
    },
    "Neon": {
        "styles": ["Neon", "Cyberpunk", "Electric"],
        "color_mood": "Electric Neon",
        "lighting": "Neon",
        "enhancement": "glowing neon signs, electric colors, night scenes, vibrant reflections"
    },
    "Mechanical": {
        "styles": ["Mechanical", "Technical Drawing", "Industrial"],
        "color_mood": "Monochrome",
        "lighting": "Studio",
        "enhancement": "precise mechanisms, technical blueprints, engineered parts, gears and pistons"
    },
    "Industrial": {
        "styles": ["Industrial", "Brutalism", "Utilitarian"],
        "color_mood": "Grays & Rust",
        "lighting": "Harsh",
        "enhancement": "machinery, metal textures, functional design, exposed pipes, concrete"
    },
    "Holographic": {
        "styles": ["Futuristic", "Digital Art", "Sci-Fi"],
        "color_mood": "Iridescent & Translucent",
        "lighting": "Holographic",
        "enhancement": "translucent projections, light-based interfaces, shimmering data"
    },
    "Biomechanical": {
        "styles": ["Biopunk", "H.R. Giger", "Surrealism"],
        "color_mood": "Organic & Metallic",
        "lighting": "Organic Glow",
        "enhancement": "fusion of flesh and machine, organic technology, alien-like structures"
    },

    # --- Vintage & Retro ---
    "Retro": {
        "styles": ["Retro Futurism", "Mid-Century Modern", "Pop Art"],
        "color_mood": "70s Oranges & Browns",
        "lighting": "Natural",
        "enhancement": "nostalgic colors, classic design, period styling, distinct era feel"
    },
    "Vintage": {
        "styles": ["Vintage Photography", "Antique", "Classic"],
        "color_mood": "Faded Sepia",
        "lighting": "Golden hour",
        "enhancement": "aged patina, classic elegance, timeless beauty, worn textures"
    },
    "Sepia": {
        "styles": ["Sepia", "Vintage", "Antique"],
        "color_mood": "Sepia Tones",
        "lighting": "Soft",
        "enhancement": "sepia tones, aged photographs, nostalgic warmth, old-timey feel"
    },
    "Film_Noir": {
        "styles": ["Film Noir", "Chiaroscuro", "Hardboiled"],
        "color_mood": "High-Contrast Monochrome",
        "lighting": "Low Key",
        "enhancement": "femme fatale, Venetian blinds shadows, smoke, mystery, cynical mood"
    },
    "Art_Deco": {
        "styles": ["Art Deco", "Roaring Twenties", "Geometric"],
        "color_mood": "Gold, Black, & Silver",
        "lighting": "Theatrical",
        "enhancement": "streamlined forms, geometric patterns, luxury materials, symmetrical designs"
    },
    "Mid_Century_Modern": {
        "styles": ["Mid-Century Modern", "Googie Architecture", "Retro"],
        "color_mood": "Teal, Orange, & Walnut",
        "lighting": "Natural",
        "enhancement": "clean lines, organic shapes, minimalist decoration, large windows"
    },
    "Atomic_Age": {
        "styles": ["Atomic Age", "Googie", "Retro Futurism"],
        "color_mood": "Pastel & Primary",
        "lighting": "Bright",
        "enhancement": "starbursts, boomerangs, atomic models, space-age optimism"
    },
    "Psychedelic": {
        "styles": ["Psychedelic Art", "Op Art", "Surrealism"],
        "color_mood": "Kaleidoscopic",
        "lighting": "Pulsating",
        "enhancement": "swirling patterns, vibrant colors, distorted visuals, melting objects"
    },
    "Victorian": {
        "styles": ["Victorian", "Gothic Revival", "Steampunk"],
        "color_mood": "Rich & Dark",
        "lighting": "Gaslight",
        "enhancement": "ornate details, complex patterns, dark woods, intricate metalwork"
    },
    "Baroque": {
        "styles": ["Baroque", "Rococo", "Dramatic"],
        "color_mood": "Rich Golds & Reds",
        "lighting": "Chiaroscuro",
        "enhancement": "drama, exuberance, grandeur, intricate detail, dynamic movement"
    },

    # --- Natural & Organic ---
    "Nature": {
        "styles": ["Landscape Painting", "Botanical Illustration", "Organic"],
        "color_mood": "Earth tones",
        "lighting": "Natural",
        "enhancement": "natural textures, organic forms, living ecosystems, flora and fauna"
    },
    "Organic": {
        "styles": ["Organic", "Natural", "Flowing"],
        "color_mood": "Earth tones",
        "lighting": "Natural",
        "enhancement": "curved lines, natural patterns, growing forms, non-geometric"
    },
    "Earthy": {
        "styles": ["Earth Art", "Natural", "Rustic"],
        "color_mood": "Browns, Greens, & Ochres",
        "lighting": "Natural",
        "enhancement": "soil, stone, wood textures, natural materials, grounded feeling"
    },
    "Forest": {
        "styles": ["Landscape", "Nature", "Green"],
        "color_mood": "Shades of Green",
        "lighting": "Dappled Sunlight",
        "enhancement": "dense foliage, ancient trees, woodland atmosphere, moss and ferns"
    },
    "Ocean": {
        "styles": ["Seascape", "Marine Art", "Underwater Photography"],
        "color_mood": "Ocean Blues & Greens",
        "lighting": "Underwater",
        "enhancement": "crashing waves, marine life, vast horizons, oceanic depths, coral reefs"
    },
    "Mountain": {
        "styles": ["Landscape", "Alpine", "Majestic"],
        "color_mood": "Cool Grays & Blues",
        "lighting": "Alpenglow",
        "enhancement": "towering peaks, rocky terrain, alpine atmosphere, vast vistas"
    },
    "Desert": {
        "styles": ["Desert Landscape", "Arid", "Minimalist"],
        "color_mood": "Warm Oranges & Yellows",
        "lighting": "Harsh Sun",
        "enhancement": "sand dunes, cacti, sparse vegetation, heat haze, cracked earth"
    },
    "Jungle": {
        "styles": ["Tropical", "Dense", "Lush"],
        "color_mood": "Lush Greens & Vibrant Flowers",
        "lighting": "Canopy Light",
        "enhancement": "thick vegetation, exotic wildlife, humid atmosphere, hanging vines"
    },
    "Arctic": {
        "styles": ["Arctic Landscape", "Minimalist", "Cold"],
        "color_mood": "Icy Blues & Whites",
        "lighting": "Blue hour",
        "enhancement": "ice formations, glaciers, snow, polar wildlife, aurora borealis"
    },
    "Volcanic": {
        "styles": ["Volcanic", "Primordial", "Dramatic"],
        "color_mood": "Fiery Reds & Blacks",
        "lighting": "Lava Glow",
        "enhancement": "lava flows, volcanic smoke, obsidian rock, primordial landscape"
    },
    "Swamp": {
        "styles": ["Swamp", "Bayou", "Mysterious"],
        "color_mood": "Murky Greens & Browns",
        "lighting": "Foggy",
        "enhancement": "cypress trees, spanish moss, murky water, mysterious atmosphere"
    },
    "Crystalline": {
        "styles": ["Geode Art", "Crystal", "Abstract"],
        "color_mood": "Iridescent",
        "lighting": "Refractive",
        "enhancement": "crystal formations, geometric facets, translucent materials, glowing gems"
    },

    # --- Growth & Life ---
    "Healing": {
        "styles": ["Healing Art", "Soft Focus", "Abstract"],
        "color_mood": "Warm Pastels",
        "lighting": "Golden Hour",
        "enhancement": "healing process, recovery journey, mending light, gentle growth"
    },
    "Growing": {
        "styles": ["Time-lapse", "Botanical", "Development"],
        "color_mood": "Spring Greens",
        "lighting": "Natural",
        "enhancement": "sprouts, vines, unfurling leaves, sense of progress and development"
    },
    "Blooming": {
        "styles": ["Botanical Illustration", "Macro Photography", "Impressionism"],
        "color_mood": "Vibrant Floral",
        "lighting": "Morning Light",
        "enhancement": "flowers in full bloom, petals opening, vibrant colors, flourishing life"
    },
    "Flourishing": {
        "styles": ["Lush", "Abundant", "Vibrant"],
        "color_mood": "Rich & Saturated",
        "lighting": "Bright",
        "enhancement": "thriving ecosystems, abundance of life, lush landscapes, peak vitality"
    },
    "Thriving": {
        "styles": ["Vibrant", "Healthy", "Strong"],
        "color_mood": "Strong & Healthy Tones",
        "lighting": "Full Sun",
        "enhancement": "peak condition, vibrant health, strong growth, resilience"
    },
    "Living": {
        "styles": ["Documentary", "Candid", "Natural"],
        "color_mood": "Natural",
        "lighting": "Natural",
        "enhancement": "breathing, moving, interacting, full of life and activity"
    },
    "Breathing": {
        "styles": ["Meditative", "Calm", "Flowing"],
        "color_mood": "Soft & Airy",
        "lighting": "Soft",
        "enhancement": "rhythmic movement, gentle expansion and contraction, life-giving breath"
    },
    "Pulsing": {
        "styles": ["Abstract", "Generative Art", "Dynamic"],
        "color_mood": "Rhythmic Colors",
        "lighting": "Pulsing",
        "enhancement": "rhythmic glow, energy waves, heartbeat, vibrant life force"
    },
    "Rebirth": {
        "styles": ["Symbolism", "Visionary", "Mythological"],
        "color_mood": "Gold & White",
        "lighting": "Sunrise",
        "enhancement": "emerging from darkness, phoenix rising, new beginnings, transformation"
    },
    "Genesis": {
        "styles": ["Primordial", "Abstract", "Cosmic"],
        "color_mood": "Elemental",
        "lighting": "Creative Spark",
        "enhancement": "creation of worlds, forming elements, the very beginning, divine creation"
    },

    # --- Color & Light Focused ---
    "Colorful": {
        "styles": ["Pop Art", "Vibrant", "Rainbow"],
        "color_mood": "Full Spectrum",
        "lighting": "Bright",
        "enhancement": "rainbow spectrum, saturated hues, color explosion, playful palette"
    },
    "Rainbow": {
        "styles": ["Rainbow", "Spectrum", "Prismatic"],
        "color_mood": "Vibrant",
        "lighting": "Prismatic",
        "enhancement": "full spectrum, prismatic effects, color gradients, light refraction"
    },
    "Pastel": {
        "styles": ["Pastel", "Soft", "Shabby Chic"],
        "color_mood": "Soft Pastels",
        "lighting": "Soft",
        "enhancement": "soft pastels, gentle hues, delicate tones, dreamy quality"
    },
    "Monochrome": {
        "styles": ["Monochrome", "Black and White", "Grayscale"],
        "color_mood": "Monochrome",
        "lighting": "Dramatic",
        "enhancement": "single color palette, tonal variations, focus on form and texture"
    },
    "Black_White": {
        "styles": ["Black and White Photography", "Film Noir", "Classic"],
        "color_mood": "High-Contrast Monochrome",
        "lighting": "Dramatic",
        "enhancement": "high contrast, dramatic shadows, classic photography, timeless feel"
    },
    "Warm": {
        "styles": ["Warm", "Cozy", "Inviting"],
        "color_mood": "Warm tones (Reds, Oranges, Yellows)",
        "lighting": "Golden hour",
        "enhancement": "warm colors, cozy atmosphere, inviting glow, comfortable feeling"
    },
    "Cool": {
        "styles": ["Cool", "Fresh", "Calm"],
        "color_mood": "Cool tones (Blues, Greens, Purples)",
        "lighting": "Blue hour",
        "enhancement": "cool colors, fresh atmosphere, calming blues, crisp feeling"
    },
    "Bright": {
        "styles": ["Bright", "Sunny", "Cheerful"],
        "color_mood": "Vibrant",
        "lighting": "High Key",
        "enhancement": "brilliant illumination, sunny disposition, radiant light, minimal shadows"
    },
    "Light": {
        "styles": ["Light", "Airy", "Ethereal"],
        "color_mood": "Pastel",
        "lighting": "Soft",
        "enhancement": "weightless, luminous, filled with light, delicate and airy"
    },
    "Shadow": {
        "styles": ["Chiaroscuro", "Tenebrism", "Dramatic"],
        "color_mood": "Monochrome",
        "lighting": "Low Key",
        "enhancement": "dramatic shadows, silhouettes, shadow play, mystery and depth"
    },
    "Contrast": {
        "styles": ["High Contrast", "Bold", "Graphic"],
        "color_mood": "Complementary Colors",
        "lighting": "Dramatic",
        "enhancement": "stark contrasts, opposing elements, visual tension, graphic impact"
    },
    "Iridescent": {
        "styles": ["Iridescent", "Holographic", "Prismatic"],
        "color_mood": "Shifting Rainbow",
        "lighting": "Multi-directional",
        "enhancement": "mother of pearl effect, shifting colors, oil slick, shimmering surfaces"
    },
    "Fluorescent": {
        "styles": ["Fluorescent", "UV Art", "Psychedelic"],
        "color_mood": "Glowing Neon",
        "lighting": "Blacklight",
        "enhancement": "glowing under UV light, vibrant and electric, otherworldly colors"
    },

    # --- Textural & Abstract ---
    "Soft": {
        "styles": ["Soft Focus", "Sfumato", "Impressionism"],
        "color_mood": "Pastel",
        "lighting": "Diffused",
        "enhancement": "soft textures, gentle transitions, tender touch, blurred edges"
    },
    "Hard": {
        "styles": ["Hard Edge Painting", "Brutalism", "Geometric"],
        "color_mood": "High contrast",
        "lighting": "Harsh",
        "enhancement": "hard surfaces, sharp angles, rigid structures, defined lines"
    },
    "Sharp": {
        "styles": ["Hyperrealism", "Sharp Focus", "Crisp"],
        "color_mood": "High contrast",
        "lighting": "Studio",
        "enhancement": "razor-sharp details, precise edges, crystal clear focus, high definition"
    },
    "Blurred": {
        "styles": ["Soft Focus", "Motion Blur", "Bokeh"],
        "color_mood": "Pastel",
        "lighting": "Soft",
        "enhancement": "out of focus, motion blur, dreamy atmosphere, indistinct forms"
    },
    "Abstract": {
        "styles": ["Abstract", "Non-representational", "Conceptual"],
        "color_mood": "Vibrant",
        "lighting": "Natural",
        "enhancement": "abstract forms, conceptual ideas, non-literal representation, focus on color/shape"
    },
    "Flowing": {
        "styles": ["Fluid Art", "Action Painting", "Organic"],
        "color_mood": "Cool tones",
        "lighting": "Natural",
        "enhancement": "flowing movement, liquid dynamics, graceful curves, sense of motion"
    },
    "Angular": {
        "styles": ["Cubism", "Deconstructivism", "Geometric"],
        "color_mood": "High contrast",
        "lighting": "Dramatic",
        "enhancement": "sharp angles, angular forms, geometric precision, jarring lines"
    },
    "Curved": {
        "styles": ["Art Nouveau", "Organic", "Soft"],
        "color_mood": "Warm tones",
        "lighting": "Soft",
        "enhancement": "curved lines, organic shapes, soft transitions, flowing forms"
    },
    "Gritty": {
        "styles": ["Industrial", "Street Photography", "Grunge"],
        "color_mood": "Muted & Dirty",
        "lighting": "Harsh",
        "enhancement": "urban decay, rough textures, film grain, imperfections, raw feel"
    },
    "Glossy": {
        "styles": ["Hyperrealism", "Pop Art", "Modern"],
        "color_mood": "Vibrant",
        "lighting": "Studio",
        "enhancement": "shiny surfaces, reflections, high gloss finish, sleek and modern"
    },

    # --- Playful & Innocent ---
    "Childlike": {
        "styles": ["Children's Art", "Naive Art", "Innocent"],
        "color_mood": "Primary Colors",
        "lighting": "Natural",
        "enhancement": "childlike wonder, innocent perspective, simple joy, crayon drawings"
    },
    "Innocent": {
        "styles": ["Innocent", "Pure", "Clean"],
        "color_mood": "White & Pastels",
        "lighting": "Soft",
        "enhancement": "pure innocence, untainted beauty, pristine quality, gentle spirit"
    },
    "Playful": {
        "styles": ["Playful", "Fun", "Whimsical"],
        "color_mood": "Vibrant",
        "lighting": "Bright",
        "enhancement": "playful energy, fun atmosphere, lighthearted joy, sense of games"
    },
    "Fun": {
        "styles": ["Fun", "Joyful", "Cartoon"],
        "color_mood": "Bright & Cheerful",
        "lighting": "Natural",
        "enhancement": "pure fun, joyful celebration, infectious happiness, comedic"
    },
    "Celebratory": {
        "styles": ["Celebratory", "Festive", "Party"],
        "color_mood": "Vibrant & Gold",
        "lighting": "Festive Lights",
        "enhancement": "festive atmosphere, celebration, party mood, confetti and streamers"
    },
    "Festive": {
        "styles": ["Festive", "Holiday", "Celebration"],
        "color_mood": "Traditional Holiday Colors",
        "lighting": "Twinkling Lights",
        "enhancement": "festive decorations, holiday spirit, celebration, seasonal cheer"
    },
    "Cartoonish": {
        "styles": ["Cartoon", "Toon", "Animation"],
        "color_mood": "Bright & Saturated",
        "lighting": "Flat",
        "enhancement": "bold outlines, simplified shapes, exaggerated features, funny"
    },
    "Cute": {
        "styles": ["Kawaii", "Chibi", "Children's Illustration"],
        "color_mood": "Pastel Pinks & Blues",
        "lighting": "Soft",
        "enhancement": "big eyes, rounded shapes, adorable characters, sweet and charming"
    },

    # --- Damaged & Decayed ---
    "Abandoned": {
        "styles": ["Urban Exploration", "Decay", "Ruins"],
        "color_mood": "Desaturated & Dusty",
        "lighting": "Crepuscular Rays",
        "enhancement": "abandoned buildings, decay, forgotten places, dust and cobwebs"
    },
    "Forgotten": {
        "styles": ["Forgotten", "Lost", "Antique"],
        "color_mood": "Faded Vintage",
        "lighting": "Soft",
        "enhancement": "forgotten memories, lost civilizations, time's passage, overgrown ruins"
    },
    "Lost": {
        "styles": ["Lost", "Confused", "Searching"],
        "color_mood": "Foggy & Muted",
        "lighting": "Blue hour",
        "enhancement": "lost in wilderness, searching for direction, confusion, disoriented"
    },
    "Broken": {
        "styles": ["Kintsugi", "Deconstruction", "Fragmented"],
        "color_mood": "Monochrome with Gold",
        "lighting": "Dramatic",
        "enhancement": "broken pieces, shattered fragments, mended with gold, visible damage"
    },
    "Damaged": {
        "styles": ["Damaged", "Weathered", "Worn"],
        "color_mood": "Vintage",
        "lighting": "Natural",
        "enhancement": "visible damage, weathered surfaces, worn textures, scratched and torn"
    },
    "Decaying": {
        "styles": ["Decay", "Grunge", "Organic"],
        "color_mood": "Earthy & Moldy",
        "lighting": "Low Light",
        "enhancement": "rotting wood, peeling paint, rust, organic decay process"
    },
    "Withered": {
        "styles": ["Melancholic", "Symbolism", "Nature"],
        "color_mood": "Desaturated Browns",
        "lighting": "Harsh",
        "enhancement": "dried flowers, withered leaves, end of a life cycle, fragile beauty"
    },
    "Glitching": {
        "styles": ["Glitch Art", "Digital", "Abstract"],
        "color_mood": "RGB Split",
        "lighting": "Screen Flicker",
        "enhancement": "digital errors, pixel sorting, databending, visual corruption"
    },
    "Fragmented": {
        "styles": ["Cubism", "Deconstruction", "Collage"],
        "color_mood": "High Contrast",
        "lighting": "Multiple Sources",
        "enhancement": "shattered view, multiple perspectives, broken pieces reassembled"
    },

    # --- Adventure & Exploration ---
    "Adventure": {
        "styles": ["Adventure", "Action", "Exploration"],
        "color_mood": "Vibrant Naturals",
        "lighting": "Natural",
        "enhancement": "exploration, discovery, thrilling journeys, treasure maps, ancient ruins"
    },
    "Quest": {
        "styles": ["Epic Fantasy", "Adventure", "Heroic"],
        "color_mood": "Warm tones",
        "lighting": "Golden hour",
        "enhancement": "heroic journey, noble purpose, legendary quest, facing a great challenge"
    },
    "Journey": {
        "styles": ["Landscape", "Adventure", "Travel"],
        "color_mood": "Natural",
        "lighting": "Changing Times of Day",
        "enhancement": "winding paths, distant horizons, travel stories, long roads"
    },
    "Discovery": {
        "styles": ["Exploration", "Scientific Illustration", "Wonder"],
        "color_mood": "Bright & Clear",
        "lighting": "Natural",
        "enhancement": "new worlds, scientific wonder, breakthrough moments, charting the unknown"
    },
    "Mythical": {
        "styles": ["Mythological", "Fantasy", "Classical Art"],
        "color_mood": "Gold & Marble",
        "lighting": "Divine",
        "enhancement": "mythological creatures, legendary heroes, gods and goddesses, ancient myths"
    },
    "Legendary": {
        "styles": ["Epic", "Heroic", "Mythical"],
        "color_mood": "Cinematic",
        "lighting": "Dramatic",
        "enhancement": "stories told through generations, legendary figures, epic scale"
    },
    "Tribal": {
        "styles": ["Tribal Art", "Primitivism", "Ethnic"],
        "color_mood": "Earthy & Natural Pigments",
        "lighting": "Firelight",
        "enhancement": "tribal patterns, masks, body paint, ancient rituals, community"
    },
    "Ancient": {
        "styles": ["Ancient History", "Archaeology", "Hieroglyphics"],
        "color_mood": "Stone & Sand",
        "lighting": "Torchlight",
        "enhancement": "ancient ruins, historical artifacts, long-lost civilizations, sense of history"
    },
}

# This line dynamically creates the list for the selectbox from the dictionary keys.
# This is a more robust way to manage the options.
mood_preset = st.selectbox("🌙 Mood Presets", ["Custom"] + list(MOOD_PRESETS.keys()))

    
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
                    if st.button(f"View #{i+1}", key=f"view_{i}", use_container_width=True):
                        st.session_state.current_image = img_data
                        st.rerun()

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
                # Enhance prompt if requested or preset applied
                if enhance_prompt or (hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied):
                    if hasattr(st.session_state, 'preset_applied') and st.session_state.preset_applied:
                        preset = st.session_state.preset_applied
                        enhanced_prompt = f"{prompt}, {preset['styles'][0]} style, {preset['color_mood']} color palette, {preset['lighting']} lighting, {preset['enhancement']}, {quality_level} quality"
                    else:
                        enhanced_prompt = f"{prompt}, {selected_style} style, {color_mood} color palette, {lighting} lighting, {quality_level} quality"
                else:
                    enhanced_prompt = prompt
                
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
        
        # Description if available
        if img_data.get('description'):
            st.markdown("### 📝 AI Description")
            st.info(img_data['description'])
        
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

with col2:
    st.markdown("### 💡 Quick Tips")
    
    with st.expander("✨ Prompt Writing Guide", expanded=True):
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


st.image("k3.jpg", use_container_width=True)
st.sidebar.image("k2.jpg", use_container_width=True)
st.image("k6.jpg", use_container_width=True)
st.image("k7.jpg", use_container_width=True)
st.image("k10.jpg", use_container_width=True)
st.image("k8.jpg", use_container_width=True)
st.sidebar.image("k4.jpg", use_container_width=True)
st.sidebar.image("k15.jpg", use_container_width=True)
st.image("k16.jpg", use_container_width=True)
st.image("k13.jpg", use_container_width=True)
st.image("k14.jpg", use_container_width=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
    <p>✨ Powered by Google Gemini Flash • Created with ❤️ for artists and dreamers</p>
    <p style="font-size: 0.8rem;">Transform your imagination into reality with AI-powered artistry</p>
</div>
""", unsafe_allow_html=True)
