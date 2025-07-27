<div align="center">
<img src="https://raw.githubusercontent.com/your-username/your-repo-name/main/k11.jpg?raw=true" alt="DreamCanvas Banner" width="800"/>
<br/>
<h1 style="font-size: 4rem; font-weight: bold; text-align: center; background: linear-gradient(90deg, #7fa4ff 0%, #4cd9c0 33%, #ffea5d 66%, #ff8a65 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
DreamCanvas
</h1>
<p align="center">
<strong>An extraordinarily advanced AI image generation suite powered by Google Gemini.</strong>
<br />
<em>Transforming imagination into reality, one masterpiece at a time.</em>
</p>
<p align="center">
<img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" alt="Python Version">
<img src="https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit" alt="Streamlit Version">
<img src="https://img.shields.io/badge/Gemini_API-v1-4285F4?logo=google" alt="Gemini API">
<img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>
</div>

🎨 About DreamCanvas
DreamCanvas is more than just a text-to-image application; it's a complete creative partner. This project started as my very first exploration into building an image generation app with the Google Gemini API. What began as a learning journey quickly evolved into a passion project to create one of the most feature-rich, intuitive, and aesthetically pleasing AI art studios available as a web app.

While it may be my first, I poured everything into making it a powerhouse tool for artists, designers, and dreamers. It combines the raw power of Gemini's image generation with a suite of advanced creative utilities, all wrapped in a beautiful, custom-designed cosmic interface.

<div align="center">
<img src="https://raw.githubusercontent.com/your-username/your-repo-name/main/k19.jpg?raw=true" alt="DreamCanvas Showcase" width="800"/>
</div>

✨ Key Features
DreamCanvas is packed with features that go far beyond simple image generation.

🖌️ Core Generation Engine
Feature

Description

Gemini-Powered

Leverages the cutting-edge gemini-2.0-flash-exp-image-generation model for high-quality results.

Massive Style Library

Choose from over 300+ styles across 20+ categories, from Classical Art to Cyberpunk.

Advanced Controls

Fine-tune creations with controls for aspect ratio, quality, color mood, lighting, and temperature.

Negative Prompting

Specify what you don't want to see, giving you greater control over the output.

Mood Presets

Instantly apply a cohesive aesthetic with over 100 mood presets like "Dreamy," "Cyberpunk," or "Gothic."

Prompt Auto-Enhance

Automatically enrich your prompts with selected styles and settings for more detailed results.

"Surprise Me!" Button

Spark your creativity with a powerful, context-aware random prompt generator.

Image Variations

Generate creative variations of any existing image with a single click.

🛠️ The Creative Utility Suite
A full suite of powerful tools to edit, enhance, and analyze your images, all integrated into the app.

Utility

Function

♾️ 4x Image Upscaler

Increase the resolution of any image by 400% with a faithful, detail-preserving upscale.

↔️ Magic Expand

Seamlessly expand the canvas of your image (outpainting), letting the AI fill in the new space.

🖼️ Image-to-Prompt

Upload an image and let the AI generate a detailed, descriptive prompt to recreate it.

💬 Chat with Your Image

Upload a picture and have a conversation with the AI about its contents, style, or meaning.

🎨 Color Palette Extractor

Generate a beautiful color palette from any image, complete with hex codes.

🏞️ B&W Image Colorizer

Breathe life into black and white photos by adding realistic, AI-generated color.

✏️ Pencil Sketch Converter

Transform any photo into an artistic, hand-drawn pencil sketch.

👾 Glitch Art Generator

Apply a cool, retro, digital glitch effect with customizable intensity.

📰 Halftone Print Effect

Recreate the classic dotted print effect seen in newspapers and comics.

📝 ASCII Art Generator

Convert any image into text-based ASCII art.

🚀 User Experience & Gallery
Feature

Description

Persistent Database

Your entire gallery, favorites, and prompt history are automatically saved locally using TinyDB.

Advanced Filtering

Effortlessly search your gallery, favorites, and history by keyword, style, or date.

Stunning UI/UX

A beautiful, custom-built "cosmic aesthetic" theme with animations, glass morphism, and a unique color palette.

Text-to-Speech

Listen to the AI's description of your generated images with an integrated audio player.

Multiple Export Options

Download creations as high-quality PNG, JPG, or WebP files, along with a JSON file containing all generation metadata.

💻 Tech Stack
Technology

Purpose

Python

Core application logic.

Streamlit

Building the interactive web application front-end.

Google Gemini API

The heart of the AI for image generation and analysis.

Pillow (PIL)

Powerful image manipulation and processing.

TinyDB

A lightweight, pure-Python database for data persistence.

NumPy & Scikit-learn

Powering the Color Palette Extractor.

gTTS (Google Text-to-Speech)

Generating audio for AI image descriptions.

HTML/CSS

Advanced, custom styling to create the unique user interface.

⚙️ Setup & Installation
Get DreamCanvas running on your local machine in a few simple steps.

Prerequisites
Python 3.9+

An active Google Gemini API key.

Installation Guide
Clone the repository:

git clone https://github.com/your-username/DreamCanvas.git
cd DreamCanvas

(Remember to replace your-username with your actual GitHub username!)

Create a virtual environment (recommended):

# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

Install the required libraries:
First, create a requirements.txt file in the root of the project with the following content:

streamlit
google-generativeai
Pillow
tinydb
numpy
scikit-learn
gTTS

Then, run the installation command:

pip install -r requirements.txt

Set up your Gemini API Key:

Create a folder named .streamlit in the root of your project directory.

Inside this folder, create a file named secrets.toml.

Add your API key to this file:

gemini_api_key = "YOUR_API_KEY_HERE"

Run the application:

streamlit run app.py

Your browser should open with the DreamCanvas application running!

🌟 Project Philosophy
This project is a testament to the power of passion-driven learning. As my first venture into text-to-image generation, the goal was to push the boundaries of what a Streamlit application could be. I didn't want to build just another demo; I wanted to create a holistic tool that felt like a true creative partner—a place where technology and artistry could merge seamlessly. Every feature, from the database persistence to the custom CSS, was a new challenge and a new opportunity to learn and grow.

I hope DreamCanvas inspires you as much as building it inspired me.

❤️ Acknowledgements & Contributing
This project stands on the shoulders of giants. A huge thank you to the teams behind Streamlit and Google Gemini for creating such incredible and accessible tools.

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

📜 License
This project is licensed under the MIT License - see the LICENSE.md file for details.

<div align="center">
<em>Made with ❤️ and a lot of imagination.</em>
</div>
