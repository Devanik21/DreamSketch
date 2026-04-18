# Security Model

## Key Management
API keys are loaded via Streamlit secrets (`.streamlit/secrets.toml`) and are never exposed to the client-side.

## Data Privacy
All generated images are stored locally in the instance running the server. No remote telemetry is sent back to third parties except for standard API requests to Google Gemini.
