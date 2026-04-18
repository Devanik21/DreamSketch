# Data Model

## Schema
The database uses TinyDB with the following structure:
- **ID**: UUID string
- **Prompt**: Text string
- **Image Path**: Local path to saved image
- **Metadata**: JSON object containing generation parameters (e.g., style, theme, seed)
- **Timestamp**: ISO 8601 string
