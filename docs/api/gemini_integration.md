# Gemini Integration API

## Service: Generative Image Generation
Endpoint: `gemini-2.0-flash-exp-image-generation`

## Request Structure
```json
{
  "prompt": "string",
  "negative_prompt": "string",
  "aspect_ratio": "string",
  "guidance_scale": "float"
}
```

## Response Structure
```json
{
  "image": "base64_string",
  "seed": "integer",
  "safety_ratings": "array"
}
```
