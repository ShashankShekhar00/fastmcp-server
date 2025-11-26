# FastMCP Server

**Production-Ready Model Context Protocol Implementation with OAuth 2.0**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13-purple.svg)](https://github.com/jlowin/fastmcp)
[![OAuth 2.0](https://img.shields.io/badge/OAuth-2.0-green.svg)](https://oauth.net/2/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Model Context Protocol (MCP) server enabling AI agents to execute tools securely. Built with FastMCP, featuring OAuth 2.0 authentication, SQLite database, and comprehensive security controls.

---

## Overview

This MCP server provides 4 secure tools for AI agents:
- **File Operations** (public) - Secure file read/write with path validation
- **Weather** (public) - OpenWeatherMap API integration
- **Notes** (OAuth-protected) - Personal notes management with tagging
- **Profile** (OAuth-protected) - User profile management

### Key Features

**Security First**
- OAuth 2.0 authentication with Auth0 JWT validation
- Path traversal protection and file validation
- User data isolation
- Environment-based secrets

**Production Ready**
- Docker and Docker Compose support
- Multi-stage builds (~150MB image)
- Health monitoring
- Comprehensive error handling
- Structured logging

**Database Integration**
- SQLite with SQLAlchemy ORM
- 3 models: User, Profile, Note
- Context-managed sessions

---

## Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:** Docker 20.10+ and Docker Compose 2.0+

```bash
# Clone repository
git clone https://github.com/ShashankShekhar00/fastmcp-server.git
cd fastmcp-server

# Configure environment
cp .env.example .env
# Edit .env with your Auth0 and OpenWeatherMap credentials

# Start server
docker compose up --build -d

# View logs
docker compose logs -f

# Check health
curl http://localhost:8000/mcp
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

---

### Option 2: Local Development

**Prerequisites:** Python 3.12+, Auth0 account, OpenWeatherMap API key

```bash
# Clone and setup
git clone https://github.com/ShashankShekhar00/fastmcp-server.git
cd fastmcp-server

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
python -m src.server_oauth
```

Server starts on `http://localhost:8000`

---
## Configuration

Create `.env` file with your credentials:

```env
# OAuth 2.0 (Auth0)
OAUTH_DOMAIN=dev-example.auth0.com
OAUTH_CLIENT_ID=your_client_id
OAUTH_CLIENT_SECRET=your_client_secret
OAUTH_AUDIENCE=https://api.mcp-server.com
OAUTH_TOKEN_URL=https://dev-example.auth0.com/oauth/token
OAUTH_JWKS_URL=https://dev-example.auth0.com/.well-known/jwks.json
OAUTH_ISSUER=https://dev-example.auth0.com/

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_api_key

# File Operations Security
ALLOWED_FILE_PATHS=C:\Users\YourName\Desktop,C:\Users\YourName\Downloads
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_EXTENSIONS=.txt,.json,.csv,.md

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./mcp_server.db

# Security
SECRET_KEY=your_secret_key_here
```

---

## MCP Tools

### Public Tools (No Authentication Required)

#### 1. File Operations

Secure file read/write with path validation.

```json
{
  "name": "file_operations",
  "arguments": {
    "operation": "read",
    "filepath": "C:\\Users\\YourName\\Desktop\\example.txt"
  }
}
```

```json
{
  "name": "file_operations",
  "arguments": {
    "operation": "write",
    "filepath": "C:\\Users\\YourName\\Desktop\\output.txt",
    "content": "Hello, World!"
  }
}
```

**Features:**
- Path allowlist validation
- File extension whitelist
- 10MB size limit
- Metadata extraction

#### 2. Weather

OpenWeatherMap API integration.

```json
{
  "name": "weather",
  "arguments": {
    "city": "London"
  }
}
```

**Returns:** Temperature, humidity, wind speed, weather conditions

### OAuth-Protected Tools (Requires Bearer Token)

#### 3. Notes

Personal notes management with CRUD operations.

```json
{
  "name": "notes",
  "arguments": {
    "action": "create",
    "content": "My note",
    "title": "Important",
    "tags": ["work", "urgent"]
  }
}
```

**Operations:** create, get, list, update, delete, archive, unarchive, pin, unpin

#### 4. Profile

User profile management.

```json
{
  "name": "profile",
  "arguments": {
    "action": "create",
    "name": "John Doe",
    "bio": "Software Developer"
  }
}
```

**Operations:** get, create, update, delete

---
## Project Structure

```
fastmcp-server/
├── src/
│   ├── server_oauth.py        # Main FastMCP server (ACTIVE)
│   ├── config.py              # Configuration management
│   ├── auth/                  # OAuth 2.0 & JWT validation
│   ├── database/              # SQLAlchemy session management
│   ├── models/                # User, Profile, Note models
│   ├── services/              # Business logic layer
│   ├── tools/                 # 4 MCP tools
│   └── utils/                 # Errors, logging, validators
├── scripts/                   # Testing & utility scripts
├── Dockerfile                 # Multi-stage container build
├── docker-compose.yml         # Orchestration
├── healthcheck.py             # Docker health monitoring
└── requirements.txt           # Python dependencies
```

### Key Components

- **FastMCP** - MCP protocol implementation (HTTP transport)
- **SQLAlchemy** - ORM with SQLite database
- **Auth0** - OAuth 2.0 authentication provider
- **JWT Validation** - Token verification with JWKS
- **Docker** - Containerization with multi-stage builds

---

## Testing

```bash
# Test OAuth flow
python scripts/test_oauth.py

# Test OAuth-protected tools
python scripts/test_oauth_tools.py

# Test weather API
python scripts/test_weather_api.py

# Test file operations
python scripts/test_tools.py

# Use tools locally
python scripts/use_tools_locally.py
```

---

## Docker Deployment

### Using Docker Compose

```bash
docker compose up --build -d
```

### Manual Docker Build

```bash
# Build image
docker build -t fastmcp-server .

# Run container
docker run -p 8000:8000 --env-file .env fastmcp-server
```

### Health Check

```bash
curl http://localhost:8000/mcp
```

See [DOCKER.md](DOCKER.md) for advanced Docker configuration, deployment options, and troubleshooting.

---

## Security Features

- OAuth 2.0 JWT authentication with Auth0
- Path traversal protection
- File extension validation (whitelist)
- File size limits (10MB default)
- Configurable path allowlists
- User data isolation
- Token redaction in logs
- Environment-based secrets
- Non-root Docker user

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Protocol | FastMCP 2.13 |
| Language | Python 3.12+ |
| Database | SQLite + SQLAlchemy |
| Auth | OAuth 2.0 (Auth0) |
| Container | Docker + Docker Compose |
| APIs | OpenWeatherMap |

---

## Documentation

- **[README.md](README.md)** - This file (quick start)
- **[PROJECT_INVENTORY.md](PROJECT_INVENTORY.md)** - Complete project overview
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Quick Docker setup
- **[DOCKER_QUICKREF.md](DOCKER_QUICKREF.md)** - Docker command reference
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing documentation

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP protocol implementation
- [Auth0](https://auth0.com/) - Authentication platform
- [OpenWeatherMap](https://openweathermap.org/) - Weather data API
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit

---

## Contact

**Shashank Shekhar**
- GitHub: [@ShashankShekhar00](https://github.com/ShashankShekhar00)
- Repository: [fastmcp-server](https://github.com/ShashankShekhar00/fastmcp-server)

---

*Production-ready MCP server with OAuth 2.0, Docker support, and comprehensive security controls.*
