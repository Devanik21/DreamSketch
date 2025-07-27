# 🌈 DreamCanvas • Powered by Imagination

<div align="center">
 
  <br/>
  <h1 style="font-size: 4rem; font-weight: bold; text-align: center; background: linear-gradient(90deg, #7fa4ff 0%, #4cd9c0 33%, #ffea5d 66%, #ff8a65 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">DreamCanvas</h1>
  <p><strong>An extraordinarily advanced AI image generation suite powered by Google Gemini.</strong><br/><em>Transforming imagination into reality, one masterpiece at a time.</em></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" />
    <img src="https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit" />
    <img src="https://img.shields.io/badge/Gemini_API-v1-4285F4?logo=google" />
    <img src="https://img.shields.io/badge/License-MIT-green" />
  </p>
</div>

## 🎨 About DreamCanvas

DreamCanvas is more than just a text-to-image app—it's a creative partner. As my **first project using the Google Gemini API**, it began as a learning experiment and grew into a feature-rich, artist-friendly AI art studio with an ethereal cosmic aesthetic.

<div align="center">
  
</div>

## ✨ Key Features

### 🖌️ Core Generation Engine

| Feature               | Description                                                              |
| --------------------- | ------------------------------------------------------------------------ |
| Gemini-Powered        | Uses `gemini-2.0-flash-exp-image-generation` for stunning image quality. |
| Massive Style Library | 300+ styles across 20+ themes like Classical, Vaporwave, Cyberpunk, etc. |
| Advanced Controls     | Customize aspect ratio, color mood, lighting, temperature, and more.     |
| Negative Prompting    | Eliminate unwanted elements from your output.                            |
| Mood Presets          | One-click aesthetic vibes like "Dreamy", "Gothic", "Fantasy", and more.  |
| Prompt Auto-Enhance   | Enriches your text prompts with intelligent enhancements.                |
| "Surprise Me!" Button | Context-aware random prompt generator.                                   |
| Image Variations      | Create fresh takes on existing images with one click.                    |

### 🛠️ Creative Utility Suite

| Utility                    | Function                                                            |
| -------------------------- | ------------------------------------------------------------------- |
| ♾️ 4x Image Upscaler       | Boost resolution by 4x while preserving detail.                     |
| ↔️ Magic Expand            | Outpaint images to expand the canvas naturally.                     |
| 🖼️ Image-to-Prompt        | Extract descriptive prompts from uploaded images.                   |
| 💬 Chat with Image         | Converse with the AI about any image's style, elements, or meaning. |
| 🎨 Color Palette Extractor | Extract beautiful palettes with hex codes from images.              |
| 🏞️ B\&W Image Colorizer   | Add life to grayscale images with vivid color.                      |
| ✏️ Pencil Sketch           | Turn images into delicate pencil-style sketches.                    |
| 👾 Glitch Art Generator    | Apply custom glitch effects for a retro vibe.                       |
| 📰 Halftone Effect         | Recreate a classic newspaper print effect.                          |
| 📝 ASCII Art Generator     | Convert images into mesmerizing ASCII art.                          |
| ✂️ Background Remover       | Automatically remove the background from an image.                 |

### 🚀 Gallery & User Experience

| Feature             | Description                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| Persistent Database | Local data storage via TinyDB for gallery, favorites, and history.          |
| Advanced Filtering  | Search across history and favorites by style, keyword, or time.             |
| Cosmic UI           | Glass morphism + animation + dreamy color palette for a magical experience. |
| Text-to-Speech      | Play audio descriptions of AI-generated art.                                |
| Export Options      | Download as PNG, JPG, WebP, or with JSON metadata.                          |

## 💻 Tech Stack

| Tech                 | Purpose                               |
| -------------------- | ------------------------------------- |
| Python               | Core logic                            |
| Streamlit            | Interactive frontend                  |
| Google Gemini API    | Image generation engine               |
| Pillow (PIL)         | Image manipulation                    |
| TinyDB               | Local persistent storage              |
| NumPy + Scikit-learn | Palette analysis and color clustering |
| gTTS                 | Google Text-to-Speech integration     |
| HTML/CSS             | Beautiful, custom cosmic-themed UI    |

## ⚙️ Setup & Installation

### Prerequisites

* Python 3.9+
* A valid Google Gemini API key

### Installation Guide

```bash
git clone https://github.com/your-username/DreamCanvas.git
cd DreamCanvas

# Create virtual environment (recommended)
python -m venv venv
# For Windows:
./venv/Scripts/activate
# For macOS/Linux:
source venv/bin/activate

# Add dependencies
echo streamlit > requirements.txt
echo google-generativeai >> requirements.txt
echo Pillow >> requirements.txt
echo tinydb >> requirements.txt
echo numpy >> requirements.txt
echo scikit-learn >> requirements.txt
echo gTTS >> requirements.txt

# Install libraries
pip install -r requirements.txt
```

### Add Gemini API Key

Create `.streamlit/secrets.toml` file:

```toml
gemini_api_key = "YOUR_API_KEY_HERE"
```

### Run the App

```bash
streamlit run app.py
```

Then open in your browser ✨

## 🌟 Project Philosophy

DreamCanvas is my **first** journey into the world of text-to-image generation. It's more than a demo—it's a love letter to creativity and AI, built to feel like an intuitive art companion. From prompt engineering to gallery storage, every detail was hand-crafted and custom-coded to make this experience magical and memorable.

## ❤️ Acknowledgements & Contributing

A big thank you to:

* Google for the Gemini API
* The Streamlit team for such an amazing open-source tool

Open to contributions and feedback! Please check the [issues](https://github.com/Devanik21/DreamCanvas/issues) page to get started.

## 📜 License

This project is under the [MIT License](LICENSE.md).

---

<div align="center">
  <em>Made with AI and a lot of imagination.</em>
</div>
