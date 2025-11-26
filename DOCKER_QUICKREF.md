# 🚀 Docker Quick Reference

## ⚡ One-Line Deploy

```bash
cp .env.example .env && nano .env && docker compose up --build -d
```

---

## 📋 Essential Commands

### Start/Stop
```bash
docker compose up -d              # Start in background
docker compose up --build -d      # Rebuild and start
docker compose down               # Stop and remove
docker compose down -v            # Stop and remove volumes
docker compose restart            # Restart services
```

### Monitor
```bash
docker compose logs -f            # Follow logs
docker compose logs --tail=50     # Last 50 lines
docker compose ps                 # Service status
docker stats fastmcp-server       # Resource usage
```

### Health
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' fastmcp-server

# Test endpoint
curl http://localhost:8000/mcp

# Run test script
python test_docker.py
```

### Debug
```bash
docker exec -it fastmcp-server bash           # Enter container
docker exec fastmcp-server python --version   # Run command
docker compose logs mcp-server | grep ERROR   # Find errors
```

### Data Management
```bash
# Backup
docker cp fastmcp-server:/app/data/mcp_server.db ./backup_$(date +%Y%m%d).db

# Restore
docker cp ./backup.db fastmcp-server:/app/data/mcp_server.db

# View volumes
docker volume ls
docker volume inspect fastmcp-server_mcp-data
```

---

## 🔧 Configuration

### Required in `.env`:
```env
OAUTH_DOMAIN=your-domain.auth0.com
OAUTH_CLIENT_ID=your-id
OAUTH_CLIENT_SECRET=your-secret
OAUTH_AUDIENCE=your-audience
OAUTH_TOKEN_URL=https://your-domain.auth0.com/oauth/token
OAUTH_JWKS_URL=https://your-domain.auth0.com/.well-known/jwks.json
OAUTH_ISSUER=https://your-domain.auth0.com/

OPENWEATHER_API_KEY=your-key

SECRET_KEY=generate-with-openssl-rand-hex-32

ALLOWED_FILE_PATHS=/app/data,/tmp
```

### Generate Secret Key:
```bash
openssl rand -hex 32
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `netstat -ano \| findstr :8000` then kill process |
| Container unhealthy | `docker compose logs mcp-server` |
| Permission denied | `docker exec -u root fastmcp-server chown -R mcpuser /app/data` |
| .env not found | `cp .env.example .env` |
| Build fails | `docker compose build --no-cache` |

---

## 📊 Success Indicators

✅ **Container Status**: `docker compose ps` shows "Up (healthy)"  
✅ **Logs**: Shows "All tools initialized successfully"  
✅ **Endpoint**: `curl localhost:8000/mcp` responds  
✅ **Health**: `docker inspect` shows "healthy"  
✅ **Test**: `python test_docker.py` passes  

---

## 🎯 Quick Tests

```bash
# 1. Start server
docker compose up -d

# 2. Wait 10 seconds
sleep 10

# 3. Check health
docker compose ps

# 4. Test endpoint
curl http://localhost:8000/mcp

# 5. View logs
docker compose logs --tail=20
```

Expected log output:
```
INFO:src.tools.file_operations:FileOperationsTool initialized
INFO:src.tools.weather:WeatherTool initialized
INFO:src.tools.notes:NotesTool initialized
INFO:src.tools.profile:ProfileTool initialized
INFO:__main__:All tools initialized successfully
```

---

## 📦 Files Created

```
fastmcp-server/
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Orchestration
├── .dockerignore               # Build optimization
├── healthcheck.py              # Health monitoring
├── test_docker.py              # Deployment test
├── .env.example                # Config template
├── DOCKER.md                   # Full documentation
├── DOCKER_SETUP.md             # Setup guide
└── DOCKER_FILES_SUMMARY.md     # Architecture overview
```

---

## 🚀 For Resume/GitHub

```markdown
## Docker Deployment

Production-ready Docker configuration with:
- Multi-stage optimized builds
- Health monitoring
- Persistent volumes
- Non-root security
- Complete orchestration

### Quick Start
\`\`\`bash
docker compose up --build -d
\`\`\`

See [DOCKER.md](DOCKER.md) for details.
```

---

## 💡 Pro Tips

1. **Always check logs first**: `docker compose logs -f`
2. **Health checks are your friend**: Monitor with `docker compose ps`
3. **Volumes persist data**: Don't use `-v` flag unless you want to reset
4. **Use `.env` file**: Never commit secrets
5. **Test before push**: Run `python test_docker.py`

---

## 🎓 Learn More

- Full guide: [DOCKER.md](DOCKER.md)
- Setup walkthrough: [DOCKER_SETUP.md](DOCKER_SETUP.md)
- Architecture: [DOCKER_FILES_SUMMARY.md](DOCKER_FILES_SUMMARY.md)

---

## ✅ Deployment Checklist

Before pushing to GitHub:

- [ ] `.env.example` has all required variables
- [ ] `.env` is in `.gitignore`
- [ ] `docker compose up --build -d` works
- [ ] `python test_docker.py` passes
- [ ] Health check shows "healthy"
- [ ] README.md mentions Docker
- [ ] All Docker files committed

---

**Quick help**: See [DOCKER_SETUP.md](DOCKER_SETUP.md) for step-by-step guide.
