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
    page_title="🖼️ GenAI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Then add this CSS to make sidebar wider:
st.markdown("""
<style>
.css-1d391kg {
    width: 350px !important;  /* Make sidebar wider */
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

# Ultra-beautiful dark mode CSS - Masterpiece Edition
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }
    
    :root {
        /* Ultra-soft color palette for maximum eye comfort */
        --midnight-void: #0B0B0F;
        --deep-space: #101014;
        --nebula-mist: #1A1A1F;
        --cosmic-dust: #2A2A30;
        --starlight: #3A3A42;
        
        /* Ethereal accent colors - very soft and comfortable */
        --aurora-purple: rgba(138, 143, 234, 0.8);
        --aurora-cyan: rgba(103, 232, 249, 0.7);
        --aurora-pink: rgba(244, 114, 182, 0.6);
        --aurora-green: rgba(129, 230, 217, 0.7);
        --aurora-orange: rgba(251, 191, 36, 0.6);
        
        /* Text colors optimized for dark mode comfort */
        --text-primary: #E8EAF0;
        --text-secondary: #C1C7D0;
        --text-muted: #9CA3AF;
        --text-ultra-soft: #6B7280;
        
        /* Glass effects */
        --glass-ultra-light: rgba(255, 255, 255, 0.02);
        --glass-light: rgba(255, 255, 255, 0.04);
        --glass-medium: rgba(255, 255, 255, 0.08);
        --glass-border: rgba(255, 255, 255, 0.06);
        
        /* Soft glows */
        --glow-soft: rgba(138, 143, 234, 0.15);
        --glow-medium: rgba(138, 143, 234, 0.25);
        --glow-strong: rgba(138, 143, 234, 0.35);
    }
    /* Simple fix for dropdown text truncation */
.stSelectbox {
    width: 100% !important;
}

.stSelectbox > div {
    width: 100% !important;
}

.stSelectbox > div > div {
    width: 100% !important;
    min-width: 200px !important;
}

.stSelectbox > div > div > div {
    white-space: nowrap !important;
    text-overflow: unset !important;
    overflow: visible !important;
    color: white !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
}

/* Ensure dropdown options are also visible */
div[data-baseweb="menu"] {
    min-width: 200px !important;
    background: #1a1a1f !important;
}

div[data-baseweb="menu"] li {
    color: white !important;
    white-space: nowrap !important;
    padding: 8px 12px !important;
}





    /* Main app with ultra-smooth animated background */
    .stApp {
        background: 
            radial-gradient(ellipse 150% 100% at 50% 0%, var(--nebula-mist) 0%, var(--midnight-void) 40%),
            linear-gradient(135deg, var(--deep-space) 0%, var(--midnight-void) 100%);
        background-attachment: fixed;
        color: var(--text-primary);
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    /* Subtle animated aurora in background */
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 25% 25%, var(--aurora-purple) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, var(--aurora-cyan) 0%, transparent 50%),
            radial-gradient(circle at 75% 25%, var(--aurora-pink) 0%, transparent 45%),
            radial-gradient(circle at 25% 75%, var(--aurora-green) 0%, transparent 45%);
        opacity: 0.15;
        animation: aurora 60s ease-in-out infinite;
        pointer-events: none;
        z-index: -2;
        filter: blur(80px);
    }
    
    @keyframes aurora {
        0%, 100% { 
            transform: rotate(0deg) scale(1);
            opacity: 0.1;
        }
        25% { 
            transform: rotate(90deg) scale(1.1);
            opacity: 0.2;
        }
        50% { 
            transform: rotate(180deg) scale(0.9);
            opacity: 0.15;
        }
        75% { 
            transform: rotate(270deg) scale(1.05);
            opacity: 0.18;
        }
    }
    
    /* Ultra-soft floating particles */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(1px 1px at 25px 35px, rgba(255, 255, 255, 0.03), transparent),
            radial-gradient(0.5px 0.5px at 65px 85px, var(--aurora-cyan), transparent),
            radial-gradient(0.5px 0.5px at 125px 45px, var(--aurora-purple), transparent),
            radial-gradient(0.5px 0.5px at 185px 95px, var(--aurora-pink), transparent),
            radial-gradient(1px 1px at 245px 15px, rgba(255, 255, 255, 0.02), transparent);
        background-size: 300px 200px;
        animation: gentleFloat 40s linear infinite;
        pointer-events: none;
        z-index: -1;
        opacity: 0.4;
    }
    
    @keyframes gentleFloat {
        0% { transform: translateY(0px) translateX(0px); }
        25% { transform: translateY(-20px) translateX(10px); }
        50% { transform: translateY(0px) translateX(-5px); }
        75% { transform: translateY(-15px) translateX(-10px); }
        100% { transform: translateY(0px) translateX(0px); }
    }
    
    /* Masterpiece title container */
    .title-container {
        background: 
            linear-gradient(135deg, 
                var(--glass-ultra-light) 0%, 
                var(--glass-light) 20%,
                var(--glass-ultra-light) 40%,
                var(--glass-light) 60%,
                var(--glass-ultra-light) 80%,
                var(--glass-light) 100%
            );
        backdrop-filter: blur(40px) saturate(180%);
        -webkit-backdrop-filter: blur(40px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 32px;
        padding: 4rem 3rem;
        margin: 3rem auto;
        max-width: 90%;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 32px 64px rgba(0, 0, 0, 0.4),
            0 8px 32px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05),
            inset 0 -1px 0 rgba(255, 255, 255, 0.02);
    }
    
    /* Magical rotating border effect */
    .title-container::before {
        content: '';
        position: absolute;
        inset: -2px;
        padding: 2px;
        background: 
            conic-gradient(from 0deg,
                transparent 0deg,
                var(--aurora-purple) 30deg,
                transparent 60deg,
                var(--aurora-cyan) 90deg,
                transparent 120deg,
                var(--aurora-pink) 150deg,
                transparent 180deg,
                var(--aurora-green) 210deg,
                transparent 240deg,
                var(--aurora-orange) 270deg,
                transparent 300deg,
                var(--aurora-purple) 330deg,
                transparent 360deg
            );
        border-radius: 34px;
        mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        animation: borderRotate 30s linear infinite;
        opacity: 0.6;
        z-index: -1;
    }
    
    @keyframes borderRotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* Ultra-beautiful title text */
    .title-text {
        font-size: clamp(1.8rem, 4vw, 2.8rem); /* Reduced from 2.8-4.5rem to 1.8-2.8rem */
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
        background: 
            linear-gradient(135deg,
                #FFFFFF 0%,
                var(--aurora-purple) 15%,
                var(--aurora-cyan) 30%,
                #FFFFFF 45%,
                var(--aurora-pink) 60%,
                var(--aurora-green) 75%,
                var(--aurora-orange) 90%,
                #FFFFFF 100%
            );
        background-size: 400% 400%;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: dreamyGradient 12s ease-in-out infinite;
        margin: 0;
        position: relative;
        filter: drop-shadow(0 0 20px rgba(138, 143, 234, 0.3));
    }

    .stSidebar .stMarkdown p {
    font-size: 0.2rem !important;
}
    
    @keyframes dreamyGradient {
        0%, 100% { background-position: 0% 50%; }
        20% { background-position: 80% 20%; }
        40% { background-position: 100% 80%; }
        60% { background-position: 20% 100%; }
        80% { background-position: 80% 30%; }
    }
    
    .subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        color: var(--text-secondary);
        margin-top: 1.5rem;
        opacity: 0.9;
        line-height: 1.6;
        letter-spacing: 0.01em;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
    }
    
    /* Ultra-smooth glass buttons */
    .stButton > button {
        background: 
            linear-gradient(135deg,
                var(--glass-ultra-light) 0%,
                var(--glass-light) 50%,
                var(--glass-ultra-light) 100%
            );
        backdrop-filter: blur(24px) saturate(150%);
        -webkit-backdrop-filter: blur(24px) saturate(150%);
        border: 1px solid var(--glass-border);
        color: var(--text-primary);
        padding: 1rem 2.5rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.01em;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.15),
            0 4px 12px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
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
        background: 
            linear-gradient(90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.08) 50%,
                transparent 100%
            );
        transition: left 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(138, 143, 234, 0.2),
            0 8px 24px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-color: rgba(138, 143, 234, 0.3);
        background: 
            linear-gradient(135deg,
                var(--glass-light) 0%,
                var(--glass-medium) 50%,
                var(--glass-light) 100%
            );
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(1.01);
        transition: all 0.1s ease;
    }
    
    /* Ethereal sidebar */
    .stSidebar {
        background: 
            linear-gradient(180deg,
                rgba(16, 16, 20, 0.95) 0%,
                rgba(11, 11, 15, 0.98) 100%
            );
        backdrop-filter: blur(32px) saturate(180%);
        -webkit-backdrop-filter: blur(32px) saturate(180%);
        border-right: 1px solid var(--glass-border);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.2);
    }
    
    .stSidebar > div {
        background: transparent;
    }
    
/* Dark, ultra-comfortable input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #1e1e2f !important;
    border: 1px solid #2e2e3e !important;
    border-radius: 16px !important;
    color: #f0f0f5 !important;
    padding: 1.25rem 1rem !important;
    font-size: 0.95rem;
    line-height: 1.5;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    box-shadow: 
        0 4px 20px rgba(0, 0, 0, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #888ca0 !important;
    opacity: 0.8;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #8a8fea !important;
    box-shadow: 
        0 0 0 4px rgba(138, 143, 234, 0.12),
        0 8px 32px rgba(138, 143, 234, 0.15),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    outline: none !important;
    background: #232336 !important;
    transform: translateY(-1px);
}

    
    /* Elegant select boxes */
    .stSelectbox > div > div {
        background: var(--glass-ultra-light) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: rgba(138, 143, 234, 0.3) !important;
        box-shadow: 0 8px 32px rgba(138, 143, 234, 0.1);
    }
    
    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
        padding: 1rem !important;
        font-size: 0.95rem;
    }
    
    /* Beautiful checkboxes */
    .stCheckbox > label {
        color: var(--text-secondary) !important;
        font-weight: 500;
        transition: color 0.3s ease;
    }
    
    .stCheckbox:hover > label {
        color: var(--text-primary) !important;
    }
    
    .stCheckbox > label > div > div {
        background: var(--glass-ultra-light) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease;
    }
    
    .stCheckbox > label > div > div:hover {
        border-color: rgba(138, 143, 234, 0.4) !important;
        background: var(--glass-light) !important;
    }
    
    /* Sophisticated headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-primary) !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    
    .stMarkdown h3 {
        font-size: 1.6rem;
        margin-bottom: 1.5rem;
        background: 
            linear-gradient(135deg,
                var(--aurora-purple) 0%,
                var(--aurora-cyan) 50%,
                var(--aurora-pink) 100%
            );
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 2px 8px rgba(138, 143, 234, 0.2));
    }
    
    /* Dreamy expandable sections */
    .stExpander > div > div > div > div {
        background: var(--glass-ultra-light) !important;
        backdrop-filter: blur(24px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        transition: all 0.3s ease;
    }
    
    .stExpander:hover > div > div > div > div {
        background: var(--glass-light) !important;
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    
    /* Magical containers */
    .download-container {
        background: 
            linear-gradient(135deg,
                rgba(129, 230, 217, 0.08) 0%,
                rgba(103, 232, 249, 0.06) 100%
            );
        backdrop-filter: blur(24px);
        border: 1px solid rgba(129, 230, 217, 0.2);
        padding: 2rem;
        border-radius: 24px;
        margin-top: 1.5rem;
        box-shadow: 
            0 16px 48px rgba(129, 230, 217, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .download-container:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 24px 64px rgba(129, 230, 217, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    
    .image-gallery {
        background: var(--glass-ultra-light);
        backdrop-filter: blur(24px);
        border: 1px solid var(--glass-border);
        padding: 2rem;
        border-radius: 24px;
        margin: 1.5rem 0;
        box-shadow: 
            0 16px 48px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
    }
    
    .gallery-item {
        background: var(--glass-ultra-light);
        backdrop-filter: blur(16px);
        border: 1px solid var(--glass-border);
        padding: 1.25rem;
        border-radius: 16px;
        margin: 1rem 0;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
    }
    
    .gallery-item:hover {
        background: var(--glass-light);
        border-color: rgba(138, 143, 234, 0.3);
        transform: translateY(-4px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(138, 143, 234, 0.15),
            0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .gallery-item.selected {
        background: var(--glass-medium);
        border-color: rgba(138, 143, 234, 0.5);
        box-shadow: 
            0 16px 48px rgba(138, 143, 234, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    /* Ultra-soft status boxes */
    .error-box {
        background: 
            linear-gradient(135deg,
                rgba(244, 114, 182, 0.08) 0%,
                rgba(239, 68, 68, 0.06) 100%
            );
        backdrop-filter: blur(24px);
        border: 1px solid rgba(244, 114, 182, 0.2);
        padding: 1.5rem;
        border-radius: 20px;
        color: #FECACA;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(244, 114, 182, 0.1);
    }
    
    .success-box {
        background: 
            linear-gradient(135deg,
                rgba(129, 230, 217, 0.08) 0%,
                rgba(16, 185, 129, 0.06) 100%
            );
        backdrop-filter: blur(24px);
        border: 1px solid rgba(129, 230, 217, 0.2);
        padding: 1.5rem;
        border-radius: 20px;
        color: #A7F3D0;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(129, 230, 217, 0.1);
    }
    
    .info-box {
        background: 
            linear-gradient(135deg,
                rgba(138, 143, 234, 0.08) 0%,
                rgba(103, 232, 249, 0.06) 100%
            );
        backdrop-filter: blur(24px);
        border: 1px solid rgba(138, 143, 234, 0.2);
        padding: 1.5rem;
        border-radius: 20px;
        color: #C7D2FE;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(138, 143, 234, 0.1);
    }
    
    /* Perfect download button */
    .stDownloadButton > button {
        background: 
            linear-gradient(135deg,
                rgba(129, 230, 217, 0.12) 0%,
                rgba(16, 185, 129, 0.08) 100%
            ) !important;
        backdrop-filter: blur(24px);
        border: 1px solid rgba(129, 230, 217, 0.3) !important;
        color: var(--text-primary) !important;
        padding: 1rem 2rem;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        box-shadow: 
            0 12px 40px rgba(129, 230, 217, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        background: 
            linear-gradient(135deg,
                rgba(129, 230, 217, 0.2) 0%,
                rgba(16, 185, 129, 0.15) 100%
            ) !important;
        border-color: rgba(129, 230, 217, 0.5) !important;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 20px 60px rgba(129, 230, 217, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    /* Ultra-smooth scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--glass-ultra-light);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: 
            linear-gradient(135deg,
                var(--aurora-purple) 0%,
                var(--aurora-cyan) 100%
            );
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: 
            linear-gradient(135deg,
                rgba(138, 143, 234, 0.8) 0%,
                rgba(103, 232, 249, 0.8) 100%
            );
    }
    
    /* Breathing animation for loading states */
    @keyframes breathe {
        0%, 100% { 
            opacity: 0.6;
            transform: scale(1);
        }
        50% { 
            opacity: 1;
            transform: scale(1.02);
        }
    }
    
    .loading-breathe {
        animation: breathe 3s ease-in-out infinite;
    }
    
    /* Ultra-responsive design */
    @media (max-width: 768px) {
        .title-container {
            padding: 2.5rem 1.5rem;
            margin: 2rem 1rem;
            border-radius: 24px;
        }
        
        .title-text {
            font-size: 2.2rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            margin-top: 1rem;
        }
        
        .stButton > button {
            padding: 0.875rem 2rem;
        }
    }
    
    @media (max-width: 480px) {
        .title-container {
            padding: 2rem 1rem;
        }
        
        .title-text {
            font-size: 1.8rem;
        }
        
        .subtitle {
            font-size: 1rem;
        }
    }
    
    /* Smooth page transitions */
    .stApp > div {
        animation: fadeInUp 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Perfect focus states for accessibility */
    .stButton > button:focus-visible,
    .stTextInput > div > div > input:focus-visible,
    .stTextArea > div > div > textarea:focus-visible,
    .stSelectbox > div > div:focus-visible {
        outline: 2px solid var(--aurora-purple) !important;
        outline-offset: 2px !important;
    }
</style>
""", unsafe_allow_html=True)

# Ultra-beautiful title with enhanced cosmic effects
st.markdown("""
<div class="title-container">
    <h1 class="title-text">✨ GenAI Studio</h1>
    <p class="subtitle">Create breathtaking images with AI • Powered by Gemini Flash<br>🌙 Ultra-Beautiful Dark Mode Experience</p>
</div>
""", unsafe_allow_html=True)

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
    lighting = st.selectbox("💡 Lighting", [
        "Natural", "Dramatic", "Soft", "Studio", "Golden hour", 
        "Blue hour", "Neon", "Candlelight", "Harsh", "Backlit"
    ])
    
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
                # Enhance prompt if requested
                if enhance_prompt:
                    enhanced_prompt = f"{prompt}, {selected_style} style, {color_mood} color palette, {lighting} lighting, {quality_level} quality"
                else:
                    enhanced_prompt = prompt
                
                # Show enhanced prompt
                if enhance_prompt:
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
        st.markdown("### 🚀 Quick Actions")
        
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
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.7);">
    <p>✨ Powered by Google Gemini Flash • Created with ❤️ for artists and dreamers</p>
    <p style="font-size: 0.8rem;">Transform your imagination into reality with AI-powered artistry</p>
</div>
""", unsafe_allow_html=True)

