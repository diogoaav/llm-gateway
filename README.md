# LLM Gateway - Anthropic to OpenAI API Converter

A FastAPI-based gateway that receives Anthropic-style API calls and converts them to OpenAI-compatible format for forwarding to third-party providers.

## Features

- ✅ Receives Anthropic `/v1/messages` API calls
- ✅ Converts requests from Anthropic format to OpenAI format
- ✅ Forwards requests to OpenAI-compatible providers
- ✅ Converts responses back to Anthropic format
- ✅ Supports streaming responses
- ✅ Custom authentication token management
- ✅ Custom model name mapping via configuration file

## Quick Deploy

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/YOUR_USERNAME/llm-gateway/tree/main)

Replace `YOUR_USERNAME` with your GitHub username in the deploy button URL above.

## Configuration

### Environment Variables

The following environment variables are required:

- `UPSTREAM_BASE_URL`: The base URL of your OpenAI-compatible provider (e.g., `https://inference.do-ai.run`)
- `UPSTREAM_API_KEY`: The API key for your upstream provider
- `AUTH_TOKEN`: The authentication token clients must use to access this gateway
- `MODEL_MAPPING_FILE`: Path to model mapping file (default: `models.json`)

### Model Mapping

Create a `models.json` file to map custom Anthropic model names to provider model names:

```json
{
  "do-anthropic-claude-4.5-sonnet": "anthropic-claude-4.5-sonnet",
  "custom-model-name": "provider-model-name"
}
```

## Usage

### Client Configuration (claude-code)

Configure claude-code to use this gateway:

```bash
export ANTHROPIC_BASE_URL=https://your-app-name.ondigitalocean.app
export ANTHROPIC_MODEL=do-anthropic-claude-4.5-sonnet
export ANTHROPIC_AUTH_TOKEN=your-auth-token
export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
```

### API Endpoints

#### POST `/v1/messages`

Anthropic-compatible messages endpoint.

**Request Example:**
```json
{
  "model": "do-anthropic-claude-4.5-sonnet",
  "max_tokens": 1024,
  "system": "You are a helpful assistant",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "temperature": 0.7,
  "stream": false
}
```

**Response Example:**
```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! I'm doing well, thank you for asking."
    }
  ],
  "model": "do-anthropic-claude-4.5-sonnet",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 15,
    "output_tokens": 12
  }
}
```

#### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/llm-gateway.git
cd llm-gateway
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export UPSTREAM_BASE_URL=https://inference.do-ai.run
export UPSTREAM_API_KEY=your-provider-api-key
export AUTH_TOKEN=your-gateway-auth-token
```

4. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Conversion Details

### Request Conversion (Anthropic → OpenAI)

- `system` parameter → `messages` array with `role: "system"`
- `messages` array → OpenAI messages format
- `max_tokens` → `max_tokens`
- `temperature` → `temperature`
- `top_p` → `top_p`
- `stop_sequences` → `stop`
- `stream` → `stream`
- `top_k` → (not supported in OpenAI, dropped)

### Response Conversion (OpenAI → Anthropic)

- OpenAI `choices[0].message` → Anthropic `content` array
- OpenAI `finish_reason` → Anthropic `stop_reason`
- OpenAI `usage` → Anthropic `usage` (with token mapping)
- Streaming responses converted to Anthropic SSE format

## Deployment to DigitalOcean App Platform

1. Push your code to a GitHub repository
2. Click the "Deploy to DO" button above
3. Fill in the required environment variables:
   - `UPSTREAM_BASE_URL`
   - `UPSTREAM_API_KEY`
   - `AUTH_TOKEN`
4. Deploy!

Alternatively, you can deploy manually:

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Create a new app from GitHub
3. Select your repository
4. Configure environment variables
5. Deploy

## Security Considerations

- All requests must include a valid `AUTH_TOKEN` in the Authorization header
- The gateway forwards provider API keys securely (never exposed in responses)
- Consider adding rate limiting for production use
- Configure CORS appropriately for your use case

## License

MIT
