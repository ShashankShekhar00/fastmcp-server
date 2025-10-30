<div align="center">

# 🚀 FastMCP Server

### Production-Ready Model Context Protocol Implementation

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120-009688.svg)](https://fastapi.tiangolo.com/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13-purple.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OAuth 2.0](https://img.shields.io/badge/OAuth-2.0-green.svg)](https://oauth.net/2/)

*Enterprise-grade MCP server with OAuth 2.0, real-time SSE streaming, and secure tool execution*

[Features](#-features) • [Quick Start](#-quick-start) • [Demo](#-demo) • [Documentation](#-documentation) • [Architecture](#-architecture)

![MCP Server Demo](https://via.placeholder.com/800x400/1a1a1a/ffffff?text=FastMCP+Server+Demo)

</div>

---

## 📖 Overview

A **production-ready Model Context Protocol (MCP) server** that enables AI agents to execute tools securely with real-time progress feedback. Built with FastMCP and FastAPI, featuring OAuth 2.0 authentication, Server-Sent Events (SSE) streaming, and comprehensive security controls.

Perfect for building AI-powered applications that need secure file operations, weather data integration, and real-time streaming capabilities.

## ✨ Features

### 🔐 **Enterprise Security**
- **OAuth 2.0 Authentication** with Auth0 JWT validation
- Path traversal & SQL injection protection
- File extension & size validation
- Token redaction in logs
- Configurable allowlists

### 📡 **Real-Time Streaming**
- **Server-Sent Events (SSE)** for live progress updates
- No rate limiting on streams
- Progress tracking (validation → execution → completion)
- Interactive web-based test interface

### 🛠️ **Built-in Tools**
- **📁 File Operations**: Secure read/write with allowlist validation
- **🌤️ Weather API**: OpenWeatherMap integration with caching

### 🚀 **Production Ready**
- FastMCP protocol implementation
- Comprehensive error handling
- Structured logging
- Docker support
- Health checks & monitoring

## 🎯 Quick Start

### Prerequisites

- Python 3.12+
- Auth0 account (free tier works)
- OpenWeatherMap API key (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/ShashankShekhar00/fastmcp-server.git
cd fastmcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Create a `.env` file with your credentials:

```env
# OAuth 2.0 (Auth0)
OAUTH_DOMAIN=your-domain.auth0.com
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_AUDIENCE=https://api.mcp-server.com

# OpenWeatherMap
OPENWEATHER_API_KEY=your_api_key

# Security
ALLOWED_FILE_PATHS=/app/data,/app/uploads,test_output
SECRET_KEY=your_secret_key_here
```

### Run the Server

```bash
python -m src.server
```

The server will start on `http://localhost:8000`

## 🎬 Demo

### Interactive Test Interface

Visit `http://localhost:8000/test` to access the interactive SSE streaming demo:

- **Weather Streaming**: Real-time weather data with progress updates
- **File Operations**: Secure file read/write with live feedback
- **OAuth Integration**: Automatic token management

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Server info and available endpoints |
| `GET /health` | Health check with auth status |
| `GET /docs` | Interactive API documentation |
| `GET /sse` | MCP protocol endpoint |
| `GET /stream/weather` | Real-time weather streaming |
| `GET /stream/file` | Real-time file operations |
| `GET /test` | Interactive test interface |

## 📚 Documentation

### Using the MCP Tools

#### Weather Tool

```python
# Request weather data for a city
{
  "tool": "weather",
  "arguments": {
    "city": "London"
  }
}

# Response includes:
# - Temperature (Celsius & Fahrenheit)
# - Humidity, pressure, wind speed
# - Weather description
# - Timestamps
```

#### File Operations Tool

```python
# Read a file
{
  "tool": "file_operations",
  "arguments": {
    "operation": "read",
    "filepath": "test_output/data.txt"
  }
}

# Write a file
{
  "tool": "file_operations",
  "arguments": {
    "operation": "write",
    "filepath": "test_output/output.txt",
    "content": "Hello, World!"
  }
}
```

### SSE Streaming

Connect to streaming endpoints to receive real-time progress:

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/stream/weather?city=London&token=YOUR_TOKEN'
);

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log(`${data.stage}: ${data.progress}%`);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('Result:', data.result);
});
```

## 🏗️ Architecture

```
fastmcp-server/
├── src/
│   ├── auth/              # OAuth 2.0 & JWT validation
│   ├── middleware/        # Auth & rate limiting
│   ├── tools/             # MCP tools (file ops, weather)
│   ├── utils/             # Errors, logging, validators, SSE
│   └── server.py          # Main FastAPI + FastMCP server
├── scripts/               # Testing & utility scripts
├── tests/                 # Unit & integration tests
└── test_sse.html          # Interactive demo page
```

### Key Components

- **FastMCP**: MCP protocol implementation
- **FastAPI**: Web framework & API endpoints
- **Auth0**: OAuth 2.0 authentication provider
- **JWT Validation**: Token verification with JWKS
- **SSE Manager**: Real-time event streaming
- **Tool Wrappers**: Progress tracking for tool execution

## 🧪 Testing

```bash
# Run all tests
pytest

# Test OAuth flow
python scripts/test_oauth.py

# Test weather API
python scripts/test_weather_api.py

# Test SSE streaming
python scripts/test_sse_streaming.py
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t fastmcp-server .

# Run container
docker run -p 8000:8000 --env-file .env fastmcp-server
```

## 🔒 Security Features

- ✅ OAuth 2.0 JWT authentication
- ✅ Path traversal protection
- ✅ SQL injection prevention
- ✅ File extension validation
- ✅ Size limits (10MB default)
- ✅ Configurable allowlists
- ✅ Token redaction in logs
- ✅ CORS configuration
- ✅ Rate limiting support

## 📊 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI 0.120 |
| **Protocol** | FastMCP 2.13 |
| **Auth** | Auth0 OAuth 2.0 |
| **Streaming** | Server-Sent Events |
| **API** | OpenWeatherMap |
| **Language** | Python 3.12+ |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP protocol implementation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Auth0](https://auth0.com/) - Authentication platform
- [OpenWeatherMap](https://openweathermap.org/) - Weather data API

## 📧 Contact

**Shashank Shekhar** - [@ShashankShekhar00](https://github.com/ShashankShekhar00)

Project Link: [https://github.com/ShashankShekhar00/fastmcp-server](https://github.com/ShashankShekhar00/fastmcp-server)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by [Shashank Shekhar](https://github.com/ShashankShekhar00)

</div>
