import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import json
import time

# Page config
st.set_page_config(
    page_title="Imagen Style Weaver",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS matching the dark, sleek design
st.markdown("""
<style>
    .main {
        background-color: #0f0f23;
        color: white;
    }
    
    .stApp {
        background-color: #0f0f23;
    }
    
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    .title-container {
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .main-title {
        font-size: 4rem;
        font-weight: 300;
        margin: 0;
        background: linear-gradient(90deg, #4FC3F7, #BA68C8, #E91E63);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 2px;
    }
    
    .subtitle {
        color: #888;
        font-size: 1.1rem;
        margin-top: 1rem;
        font-weight: 300;
    }
    
    .section-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    .section-title {
        color: #4FC3F7;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    
    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-size: 1rem;
        padding: 1rem;
    }
    
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
    }
    
    .stSelectbox > div > div > div {
        color: white;
        background-color: #1a1a2e;
    }
    
    .format-buttons {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .format-btn {
        flex: 1;
        padding: 0.75rem;
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.05);
        color: white;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .format-btn.active {
        border-color: #FFA726;
        background: rgba(255, 167, 38, 0.2);
        color: #FFA726;
    }
    
    .format-btn:hover {
        border-color: rgba(255, 255, 255, 0.4);
        background: rgba(255, 255, 255, 0.1);
    }
    
    .generate-btn {
        background: linear-gradient(90deg, #E91E63, #4FC3F7);
        border: none;
        border-radius: 12px;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        padding: 1rem 2rem;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .generate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(233, 30, 99, 0.3);
    }
    
    .output-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        min-height: 400px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .output-placeholder {
        color: #888;
        font-size: 1.1rem;
    }
    
    .output-title {
        color: white;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
    }
    
    .creations-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 300;
        color: white;
        margin: 3rem 0 2rem 0;
        background: linear-gradient(90deg, #4FC3F7, #BA68C8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .stButton > button {
        display: none;
    }
    
    .icon-placeholder {
        width: 80px;
        height: 80px;
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        background: rgba(79, 195, 247, 0.1);
    }
    
    .icon-placeholder svg {
        width: 40px;
        height: 40px;
        color: #4FC3F7;
    }
</style>
""", unsafe_allow_html=True)

# Load secrets
try:
    gemini_api_key = st.secrets["gemini_api_key"]
    client = genai.Client(api_key=gemini_api_key)
except Exception as e:
    st.error("API key configuration error. Please check your secrets.toml file.")
    st.stop()

# Title
st.markdown("""
<div class="title-container">
    <h1 class="main-title">Imagen Style Weaver</h1>
    <p class="subtitle">Where your imagination meets the canvas of artificial intelligence.</p>
</div>
""", unsafe_allow_html=True)

# Art styles
ART_STYLES = [
    "Abstract Expressionism", "Anime", "Art Deco", "Art Nouveau", "Baroque", "Bauhaus",
    "Byzantine", "Cartoon", "Classicism", "Cubism", "Dadaism", "Digital Art",
    "Expressionism", "Fauvism", "Film Noir", "Folk Art", "Futurism", "Gothic",
    "Graffiti", "Impressionism", "Lowbrow", "Manga", "Minimalism", "Modernism",
    "Neo-Expressionism", "Neoclassicism", "Op Art", "Photo-realism", "Pop Art",
    "Post-Impressionism", "Psychedelic Rock Poster", "Realism", "Renaissance",
    "Rococo", "Romanticism", "Street Art", "Surrealism", "Symbolism", "Ukiyo-e",
    "Vector Art", "Watercolor", "Zentangle"
]

# Main layout
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    # Vision input
    st.markdown("""
    <div class="section-container">
        <div class="section-title">1. Describe Your Vision</div>
    </div>
    """, unsafe_allow_html=True)
    
    prompt = st.text_area(
        "",
        value="An astronaut meditating on a field of glowing mushrooms",
        height=120,
        label_visibility="collapsed"
    )
    
    # Style selection
    st.markdown("""
    <div class="section-container">
        <div class="section-title">2. Choose an Artistic Style</div>
    </div>
    """, unsafe_allow_html=True)
    
    selected_style = st.selectbox(
        "",
        ART_STYLES,
        index=ART_STYLES.index("Psychedelic Rock Poster"),
        label_visibility="collapsed"
    )
    
    # Output format
    st.markdown("""
    <div class="section-container">
        <div class="section-title">3. Choose an Output Format</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Format selection with custom styling
    format_col1, format_col2, format_col3 = st.columns(3)
    
    if 'selected_format' not in st.session_state:
        st.session_state.selected_format = 'JPG'
    
    with format_col1:
        if st.button("JPG", key="jpg_btn", use_container_width=True):
            st.session_state.selected_format = 'JPG'
    
    with format_col2:
        if st.button("PNG", key="png_btn", use_container_width=True):
            st.session_state.selected_format = 'PNG'
    
    with format_col3:
        if st.button("WebP", key="webp_btn", use_container_width=True):
            st.session_state.selected_format = 'WebP'
    
    # Generate button
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    if st.button("✨ Generate Image", key="generate", use_container_width=True):
        if not prompt.strip():
            st.error("Please enter a prompt to generate an image.")
        else:
            # Enhanced prompt with style
            enhanced_prompt = f"{prompt}, {selected_style} style"
            
            try:
                with st.spinner("Generating your masterpiece..."):
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp-image-generation",
                        contents=enhanced_prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["text", "image"]
                        )
                    )
                    
                    # Process response
                    image_data = None
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            image_data = part.inline_data.data
                    
                    if image_data:
                        st.session_state.generated_image = image_data
                        st.session_state.current_prompt = prompt
                        st.session_state.current_style = selected_style
                        st.success("Image generated successfully!")
                    else:
                        st.error("No image was generated. Please try again.")
            
            except Exception as e:
                error_msg = str(e).lower()
                if "api key" in error_msg:
                    st.error("Authentication Error: Please check your API key.")
                elif "quota" in error_msg or "limit" in error_msg:
                    st.error("Rate Limit: Please try again later.")
                elif "safety" in error_msg:
                    st.error("Content Policy: Please try a different prompt.")
                else:
                    st.error(f"Error: {str(e)}")

with col2:
    # Output area
    st.markdown("""
    <div class="output-container">
    """, unsafe_allow_html=True)
    
    if 'generated_image' in st.session_state:
        st.markdown('<div class="output-title">Your vision awaits</div>', unsafe_allow_html=True)
        
        # Display image
        img = Image.open(BytesIO(st.session_state.generated_image))
        st.image(img, use_column_width=True)
        
        # Download button
        if st.session_state.selected_format == 'PNG':
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            mime_type = "image/png"
            file_ext = "png"
        elif st.session_state.selected_format == 'WebP':
            buffer = BytesIO()
            img.save(buffer, format="WEBP", quality=90)
            mime_type = "image/webp"
            file_ext = "webp"
        else:  # JPG
            buffer = BytesIO()
            if img.mode == 'RGBA':
                jpg_img = Image.new('RGB', img.size, (255, 255, 255))
                jpg_img.paste(img, mask=img.split()[-1])
                jpg_img.save(buffer, format="JPEG", quality=95)
            else:
                img.save(buffer, format="JPEG", quality=95)
            mime_type = "image/jpeg"
            file_ext = "jpg"
        
        st.download_button(
            f"💾 Download {st.session_state.selected_format}",
            data=buffer.getvalue(),
            file_name=f"imagen_weaver_{int(time.time())}.{file_ext}",
            mime=mime_type,
            use_container_width=True
        )
    
    else:
        st.markdown("""
        <div class="icon-placeholder">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="output-title">Your vision awaits</div>
        <div class="output-placeholder">Your generated image will appear here.</div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Your Creations section
st.markdown('<h2 class="creations-title">Your Creations</h2>', unsafe_allow_html=True)

# Gallery placeholder
if 'generated_image' in st.session_state:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        img = Image.open(BytesIO(st.session_state.generated_image))
        st.image(img, use_column_width=True)
        st.caption(f"{st.session_state.current_style} style")
else:
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 3rem;">
        <p>Your generated images will appear here as a gallery.</p>
    </div>
    """, unsafe_allow_html=True)
