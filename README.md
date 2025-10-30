# MCP Server - Python Implementation

Production-ready Model Context Protocol (MCP) server with OAuth 2.1 security, providing AI models with secure file operations and live weather data.

## 🚀 Features

- **Two MCP Tools:**
  - 📁 **File Operations**: Secure read/write with path allowlist validation
  - 🌤️ **Weather Data**: Real-time weather from OpenWeatherMap API

- **Security:**
  - OAuth 2.0 with OAuth 2.1 security requirements (PKCE, no implicit flow)
  - Path traversal protection
  - Input validation and sanitization
  - Token/API key redaction in logs
  - Rate limiting (100 requests/hour per client)

- **Protocol:**
  - MCP-compliant JSON-RPC 2.0 responses
  - HTTP/SSE transport for remote access
  - Structured error responses with proper codes

- **Deployment:**
  - Docker containerization
  - Environment-based configuration
  - Production-ready logging

## 📋 Prerequisites

- Python 3.10+
- uv package manager
- Auth0 account (or AWS Cognito)
- OpenWeatherMap API key

## 🛠️ Installation

### 1. Clone and Setup

```powershell
# Navigate to project directory
cd fastmcp-server

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install uv
pip install uv

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env with your credentials
notepad .env
```

**Required environment variables:**

```bash
# OAuth 2.0 (Auth0)
OAUTH_DOMAIN=your-tenant.auth0.com
OAUTH_AUDIENCE=https://api.mcp-server.com
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_secret
OAUTH_TOKEN_URL=https://your-tenant.auth0.com/oauth/token
OAUTH_JWKS_URL=https://your-tenant.auth0.com/.well-known/jwks.json

# OpenWeatherMap
OPENWEATHER_API_KEY=your_api_key

# File Operations Security
ALLOWED_FILE_PATHS=C:\allowed\path1,C:\allowed\path2
ALLOWED_FILE_EXTENSIONS=.txt,.json,.csv,.md
MAX_FILE_SIZE_MB=10

# Server
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Get API Keys

**Auth0 Setup:**
1. Create Auth0 account at https://auth0.com
2. Create new API in Auth0 Dashboard
3. Create Machine-to-Machine application
4. Copy Domain, Client ID, Client Secret, and API Identifier

**OpenWeatherMap Setup:**
1. Sign up at https://openweathermap.org/api
2. Subscribe to Current Weather Data (free tier available)
3. Copy your API key from account settings

## 🧪 Testing

### Run Tool Tests

```powershell
# Test utilities
python scripts\test_utils.py

# Test tools (file operations and weather)
python scripts\test_tools.py
```

### Expected Output

```
✓ File write successful: 18 bytes written
✓ File read successful: 'Hello, MCP Server!'
✓ Path traversal blocked
✓ Invalid extension blocked
✓ Size limit enforced
✓ SQL injection blocked
✓ City validation passed
```

## 📚 Project Structure

```
fastmcp-server/
├── src/
│   ├── config.py              # Environment configuration
│   ├── server.py              # FastMCP server (to be created)
│   ├── auth/
│   │   ├── oauth.py           # OAuth 2.0 middleware (to be created)
│   │   └── dependencies.py    # FastAPI dependencies (to be created)
│   ├── tools/
│   │   ├── file_operations.py # ✅ File read/write tool
│   │   └── weather.py         # ✅ Weather data tool
│   ├── utils/
│   │   ├── errors.py          # ✅ MCP-compliant errors
│   │   ├── logging.py         # ✅ Structured logging
│   │   └── validators.py      # ✅ Input validation
│   └── middleware/
│       ├── rate_limit.py      # Rate limiting (to be created)
│       └── sse_handler.py     # SSE streaming (to be created)
├── tests/                     # Unit, integration, security tests
├── scripts/
│   ├── test_utils.py          # ✅ Utility tests
│   └── test_tools.py          # ✅ Tool tests
├── .env                       # Secrets (gitignored)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Current Status

### ✅ Completed
- [x] Project structure and configuration
- [x] Error handling with MCP-compliant responses
- [x] Structured logging with secret redaction
- [x] Input validators (path traversal, SQL injection protection)
- [x] File operations tool (read/write with allowlist)
- [x] Weather tool (OpenWeatherMap integration)

### 🚧 In Progress
- [ ] OAuth 2.0 middleware with JWT validation
- [ ] SSE streaming handler for MCP events
- [ ] FastMCP server with tool registration
- [ ] Rate limiting middleware
- [ ] Docker configuration
- [ ] Comprehensive test suite

## 🔒 Security Features

### Path Traversal Protection
```python
# These are blocked:
"../../../etc/passwd"
"..\\windows\\system32"
"%2e%2e/etc/passwd"
```

### SQL Injection Protection
```python
# These are blocked in city names:
"London; DROP TABLE--"
"Paris' OR '1'='1"
```

### Token Redaction
```python
# Logs automatically redact:
"Bearer eyJhbG..." → "Bearer <REDACTED>"
"api_key": "abc123" → "api_key": "<REDACTED>"
```

### File Size Limits
```python
# Default: 10MB max file size
# Configurable via MAX_FILE_SIZE_MB
```

## 📖 Tool Usage Examples

### File Operations Tool

**Read File:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "file_operations",
    "arguments": {
      "operation": "read",
      "filepath": "/app/data/config.json"
    }
  },
  "id": "1"
}
```

**Write File:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "file_operations",
    "arguments": {
      "operation": "write",
      "filepath": "/app/data/output.txt",
      "content": "Hello, World!"
    }
  },
  "id": "2"
}
```

### Weather Tool

**Get Weather:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "weather",
    "arguments": {
      "city": "London"
    }
  },
  "id": "3"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "city": "London",
    "country": "GB",
    "temperature_celsius": 15.2,
    "humidity_percent": 72,
    "description": "partly cloudy",
    "wind_speed_ms": 3.5
  },
  "id": "3"
}
```

## 🐛 Troubleshooting

### "Configuration Warning" on import
**Problem:** `.env` has placeholder values  
**Solution:** Update `.env` with real credentials

### "Module not found" errors
**Problem:** Virtual environment not activated  
**Solution:** Run `.venv\Scripts\Activate.ps1`

### Weather API returns 401
**Problem:** Invalid OpenWeatherMap API key  
**Solution:** Check key at https://home.openweathermap.org/api_keys

### Path not in allowlist
**Problem:** File path not in `ALLOWED_FILE_PATHS`  
**Solution:** Add directory to `.env` allowlist

## 📝 Next Steps

1. **Implement OAuth Middleware** - JWT validation with Auth0
2. **Create FastMCP Server** - Register tools and handle requests
3. **Add SSE Streaming** - Real-time event streaming
4. **Write Tests** - Unit, integration, and security tests
5. **Create Dockerfile** - Containerize the application
6. **Deploy** - Railway or AWS deployment

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the implementation guide

---

**Built with:** Python 3.12 • FastMCP 2.13 • FastAPI • Auth0 • OpenWeatherMap
