# LLM Gateway - Anthropic to OpenAI API Converter

A FastAPI-based gateway that receives Anthropic-style API calls and converts them to OpenAI-compatible format for forwarding to third-party providers.

## Features

- Web UI for managing multiple gateways (login-protected)
- Multiple gateways: each with its own upstream URL, API key, and model mapping
- Receives Anthropic-style API at `/gateway/{id}/v1/messages`
- Converts requests/responses between Anthropic and OpenAI formats
- Streaming support
- Request logs and token usage statistics per gateway
- Database-backed configuration (SQLite or PostgreSQL)

## Quick Deploy

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/diogoaav/llm-gateway/tree/main)

Deployment will create a dev database and prompt for:
- `ADMIN_USERNAME` – login username for the UI
- `ADMIN_PASSWORD` – login password for the UI

Gateway configurations are added via the UI after deployment.

## Configuration

### Environment Variables

- `ADMIN_USERNAME`: Username for UI login (default: `admin`)
- `ADMIN_PASSWORD`: Password for UI login (required)
- `DATABASE_URL`: Database connection URL (optional; defaults to SQLite). On App Platform this is set automatically when you add a dev database.

Gateways (upstream URL, API key, model names, auth token) are created and stored via the UI and database, not environment variables.

## Usage

### Web UI

1. Open `https://your-app-name.ondigitalocean.app/login` and sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD`.
2. Go to Dashboard and click **Add Gateway**.
3. Enter upstream base URL, API key, upstream model name, and custom model name. Save.
4. Use the shown **API Endpoint** and **Auth Token** for that gateway in claude-code.

### Client Configuration (claude-code)

Use the gateway’s endpoint and token from the Dashboard:

```bash
export ANTHROPIC_BASE_URL=https://your-app-name.ondigitalocean.app
export ANTHROPIC_MODEL=do-anthropic-claude-4.5-sonnet   # Your gateway’s custom model name
export ANTHROPIC_AUTH_TOKEN=<gateway-auth-token>        # That gateway’s token from the UI
export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
```

The API base URL is the same; the path includes the gateway ID: `/gateway/{gateway_id}/v1/messages`. Configure your client to use that full path (e.g. `ANTHROPIC_BASE_URL=https://your-app.ondigitalocean.app/gateway/1` so that requests go to `/gateway/1/v1/messages`).

### API Endpoints

#### POST `/gateway/{gateway_id}/v1/messages`

Anthropic-compatible messages endpoint for the given gateway. Send `Authorization: Bearer <gateway-auth-token>` or `x-api-key: <gateway-auth-token>`.

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
git clone https://github.com/diogoaav/llm-gateway.git
cd llm-gateway
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export ADMIN_PASSWORD=your-admin-password
# Optional: DATABASE_URL for PostgreSQL; default is SQLite
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

1. Push your code to a GitHub repository.
2. Click the "Deploy to DO" button above.
3. The template adds a dev database. Set:
   - `ADMIN_USERNAME`: UI login username
   - `ADMIN_PASSWORD`: UI login password
4. Deploy. Then open the app URL, go to `/login`, sign in, and add gateways via the Dashboard.

## Security Considerations

- Each gateway has its own auth token; API requests must use the correct token in the Authorization or x-api-key header.
- UI access is protected by ADMIN_USERNAME/ADMIN_PASSWORD.
- Provider API keys are stored in the database and never exposed in API responses.
- Consider rate limiting and CORS configuration for production.

## License

MIT
