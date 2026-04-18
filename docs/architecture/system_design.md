# System Design

## Overview
This document outlines the high-level architecture of the DreamCanvas system.

## Components
- **Frontend**: Streamlit application handling user interactions and rendering.
- **Backend**: Python-based business logic, state management, and API orchestration.
- **AI Integration**: Integration with Google Gemini API for generative models.
- **Storage**: TinyDB for persistent storage of gallery, history, and favorites.

## Data Flow
1. User provides prompt via Streamlit UI.
2. Backend processes prompt and queries Gemini API.
3. Generated image and metadata returned to Backend.
4. Data persisted to TinyDB and displayed to User.
