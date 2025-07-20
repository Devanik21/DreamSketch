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
    page_title="✨ GenAI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'images' not in st.session_state:
    st.session_state.images = []
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

# Custom CSS for beautiful gradients and styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
        background-size: 400% 400%;
        animation: backgroundFlow 25s ease infinite;
    }
    
    @keyframes backgroundFlow {
        0% { background-position: 0% 50%; }
        25% { background-position: 100% 50%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
        100% { background-position: 0% 50%; }
    }
    
    .title-container {
        background: linear-gradient(135deg, #1e2a4a 0%, #2d4a6b 25%, #3a5f8c 50%, #4674ad 75%, #5289ce 100%);
        background-size: 300% 300%;
        animation: gradient 15s ease infinite;
        padding: 2.5rem;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .title-text {
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        margin: 0;
        background: linear-gradient(-45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff9ff3, #54a0ff, #5f27cd);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 8s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        25% { background-position: 100% 50%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
        100% { background-position: 0% 50%; }
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #cbd5e1;
        margin-top: 0.5rem;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #475569, #64748b, #6b7280);
        color: #f1f5f9;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.5);
        background: linear-gradient(135deg, #64748b, #6b7280, #78716c);
    }
    
    .stSidebar {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 75%, #64748b 100%);
        background-size: 400% 400%;
        animation: backgroundFlow 25s ease infinite;
    }
    
    .stSidebar > div {
        background: transparent;
    }
    
    .stSelectbox > div > div {
        background: rgba(226, 232, 240, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.15);
        border-radius: 15px;
    }
    
    .stSelectbox > div > div > div {
        color: #e2e8f0 !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(226, 232, 240, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.15);
        border-radius: 15px;
        color: #e2e8f0;
        padding: 1rem;
    }
    
    .stTextArea > div > div > textarea {
        background: transparent !important;
        border: 1px solid rgba(226, 232, 240, 0.15);
        border-radius: 15px;
        color: #e2e8f0;
    }
    
    .stCheckbox > label {
        color: #e2e8f0 !important;
    }
    
    .stMarkdown h3 {
        color: #e2e8f0 !important;
    }
    
    .stExpander > div > div > div > div {
        background: rgba(226, 232, 240, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.1);
        border-radius: 15px;
    }
    
    .download-container {
        background: rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 20px;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .image-gallery {
        background: rgba(255,255,255,0.05);
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .gallery-item {
        background: rgba(255,255,255,0.1);
        padding: 0.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .gallery-item:hover {
        background: rgba(255,255,255,0.2);
        transform: translateY(-2px);
    }
    
    .gallery-item.selected {
        background: rgba(255,255,255,0.3);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .error-box {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #00d2d3, #54a0ff);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit default elements that cause rerun */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669, #047857);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
</style>
""", unsafe_allow_html=True)

# Title with animated gradient
st.markdown("""
<div class="title-container">
    <h1 class="title-text">✨ GenAI Studio</h1>
    <p class="subtitle">Create stunning images with AI • Powered by Gemini Flash</p>
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
STYLE_CATEGORIES = {
    "🎨 Artistic Styles": [
        "Oil painting", "Watercolor", "Acrylic painting", "Digital art", "Concept art",
        "Abstract art", "Impressionist", "Expressionist", "Cubist", "Surreal",
        "Pop art", "Street art", "Graffiti", "Minimalist", "Maximalist",
        "Art nouveau", "Art deco", "Baroque", "Renaissance", "Modern art"
    ],
    "📸 Photography Styles": [
        "Portrait photography", "Landscape photography", "Macro photography", "Street photography",
        "Fashion photography", "Black and white photography", "HDR photography", "Long exposure",
        "Vintage photography", "Film photography", "Polaroid", "Documentary style",
        "Commercial photography", "Fine art photography", "Architectural photography"
    ],
    "🎬 Cinematic & Visual": [
        "Cinematic", "Film noir", "Cyberpunk", "Steampunk", "Dieselpunk", "Solarpunk",
        "Vaporwave", "Synthwave", "Retrowave", "Outrun", "Glitchcore", "Liminal space",
        "Brutalist", "Futuristic", "Post-apocalyptic", "Utopian", "Dystopian"
    ],
    "🌟 Fantasy & Sci-Fi": [
        "Fantasy art", "Science fiction", "Space opera", "Cosmic horror", "Gothic",
        "Medieval fantasy", "High fantasy", "Dark fantasy", "Urban fantasy",
        "Alien worlds", "Biopunk", "Space exploration", "Time travel", "Parallel universe"
    ],
    "🎮 Game & Animation": [
        "Pixel art", "8-bit", "16-bit", "Anime style", "Manga style", "Studio Ghibli style",
        "Disney style", "Pixar style", "2D animation", "3D render", "Isometric",
        "Low poly", "Voxel art", "Game asset", "Character design", "Environment concept"
    ],
    "🏛️ Historical & Cultural": [
        "Ancient Egyptian", "Ancient Greek", "Roman", "Viking", "Samurai", "Wild West",
        "Victorian", "Edwardian", "Art deco", "1920s", "1950s retro", "1980s",
        "Traditional Japanese", "Chinese ink painting", "Indian miniature", "African tribal"
    ],
    "🌍 Nature & Landscapes": [
        "Photorealistic nature", "Dreamy landscape", "Tropical paradise", "Winter wonderland",
        "Desert landscape", "Forest scene", "Mountain vista", "Ocean scene", "Sky study",
        "Botanical illustration", "Wildlife photography", "Underwater scene", "Space landscape"
    ],
    "✨ Special Effects": [
        "Holographic", "Neon glow", "Particle effects", "Light rays", "Bokeh", "Double exposure",
        "Prism effects", "Crystal", "Glass", "Metal", "Fabric texture", "Wood texture",
        "Stone texture", "Fire effects", "Water effects", "Smoke effects", "Lightning"
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
                    st.image(img, use_column_width=True)
                
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
        
        st.image(img, caption="✨ Generated Masterpiece", use_column_width=True)
        
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
