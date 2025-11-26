# 🐳 Docker Deployment Guide

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- `.env` file configured (copy from `.env.example`)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Build and start the container
docker compose up --build -d

# 2. View logs
docker compose logs -f mcp-server

# 3. Check status
docker compose ps

# 4. Stop the container
docker compose down

# 5. Stop and remove volumes (clean slate)
docker compose down -v
```

### Option 2: Using Docker CLI

```bash
# 1. Build the image
docker build -t fastmcp-server:latest .

# 2. Run the container
docker run -d \
  --name fastmcp-server \
  -p 8000:8000 \
  --env-file .env \
  -v mcp-data:/app/data \
  -v mcp-logs:/app/logs \
  fastmcp-server:latest

# 3. View logs
docker logs -f fastmcp-server

# 4. Stop the container
docker stop fastmcp-server

# 5. Remove the container
docker rm fastmcp-server
```

## Configuration

### Environment Variables

All configuration is done via environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

- **OAUTH_DOMAIN**: Your Auth0 domain
- **OAUTH_CLIENT_ID**: Your Auth0 client ID
- **OAUTH_CLIENT_SECRET**: Your Auth0 client secret
- **OPENWEATHER_API_KEY**: Your OpenWeatherMap API key
- **SECRET_KEY**: Generate with `openssl rand -hex 32`
- **ALLOWED_FILE_PATHS**: Comma-separated list of allowed directories

### Volumes

The container uses two persistent volumes:

- **mcp-data**: Database and user data (`/app/data`)
- **mcp-logs**: Application logs (`/app/logs`)

### Ports

- **8000**: MCP server HTTP endpoint

## Health Check

The container includes a health check that runs every 30 seconds:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' fastmcp-server

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' fastmcp-server
```

## Useful Commands

### View Container Info

```bash
# Container stats (CPU, memory, network)
docker stats fastmcp-server

# Container details
docker inspect fastmcp-server

# Enter container shell
docker exec -it fastmcp-server /bin/bash
```

### Manage Data

```bash
# Backup database
docker cp fastmcp-server:/app/data/mcp_server.db ./backup.db

# Restore database
docker cp ./backup.db fastmcp-server:/app/data/mcp_server.db

# List volumes
docker volume ls

# Inspect volume
docker volume inspect fastmcp-server_mcp-data

# Backup volume
docker run --rm -v fastmcp-server_mcp-data:/data -v $(pwd):/backup busybox tar czf /backup/mcp-data-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v fastmcp-server_mcp-data:/data -v $(pwd):/backup busybox tar xzf /backup/mcp-data-backup.tar.gz -C /data
```

### Logs

```bash
# Follow logs
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100

# View logs for specific service
docker compose logs -f mcp-server

# Export logs
docker compose logs --no-color > logs.txt
```

### Update and Rebuild

```bash
# Pull latest code and rebuild
git pull
docker compose up --build -d

# Force rebuild (no cache)
docker compose build --no-cache
docker compose up -d
```

## Production Deployment

### Security Recommendations

1. **Use HTTPS**: Set `HTTPS_ONLY=true` and use a reverse proxy (nginx/traefik)
2. **Secure secrets**: Use Docker secrets or external secret management
3. **Non-root user**: Container already runs as non-root user `mcpuser`
4. **Network isolation**: Use Docker networks to isolate services
5. **Resource limits**: Add resource constraints in `docker-compose.yml`

### Resource Limits (Optional)

Add to `docker-compose.yml` under `mcp-server`:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

### Reverse Proxy (Nginx Example)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker compose logs mcp-server

# Verify environment variables
docker compose config

# Check if port is already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac
```

### Database issues

```bash
# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d

# Check database file
docker exec fastmcp-server ls -lh /app/data/
```

### Permission issues

```bash
# Fix volume permissions
docker exec -u root fastmcp-server chown -R mcpuser:mcpuser /app/data /app/logs
```

### Health check failing

```bash
# Test health endpoint manually
docker exec fastmcp-server curl http://localhost:8000/health

# Disable health check temporarily (add to docker-compose.yml)
healthcheck:
  disable: true
```

## Testing

Test the API endpoints:

```bash
# Health check
curl http://localhost:8000/health

# MCP endpoint (requires proper MCP client request)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Multi-Environment Setup

Create environment-specific compose files:

**docker-compose.dev.yml**:
```yaml
version: '3.8'
services:
  mcp-server:
    build:
      target: builder
    volumes:
      - ./src:/app/src:ro
    environment:
      - LOG_LEVEL=DEBUG
```

**docker-compose.prod.yml**:
```yaml
version: '3.8'
services:
  mcp-server:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
```

Run with:
```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build image
        run: docker build -t fastmcp-server:${{ github.sha }} .
      
      - name: Run tests
        run: docker run --rm fastmcp-server:${{ github.sha }} python -m pytest
```

## Support

For issues and questions:
- Check logs: `docker compose logs -f`
- Verify config: `docker compose config`
- Test health: `curl http://localhost:8000/health`
- GitHub Issues: [Your repo URL]
