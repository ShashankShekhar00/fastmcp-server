# CRITICAL SECURITY FIX - Auth0 Keys Exposed

## IMMEDIATE ACTIONS REQUIRED

### 1. Rotate Auth0 Credentials (DO THIS FIRST!)

**Go to Auth0 Dashboard RIGHT NOW:**
1. Navigate to: https://manage.auth0.com/
2. Go to Applications → Your Application
3. Settings → Rotate Client Secret
4. Click "Rotate" button
5. Copy the NEW client secret
6. Update your LOCAL `.env` file with new credentials

**DO NOT** push the new credentials to GitHub!

---

### 2. Clean Git History

The files `OAUTH_COMPLETE.md` and `SERVER_OAUTH_COMPLETE.md` were in your git history before deletion and likely contained real credentials.

**Option A: Using BFG Repo Cleaner (Recommended)**

```bash
# Download BFG Repo Cleaner
# https://rtyley.github.io/bfg-repo-cleaner/

# Backup your repo first
cd ..
cp -r fastmcp-server fastmcp-server-backup

# Create a fresh clone
git clone --mirror https://github.com/ShashankShekhar00/fastmcp-server.git
cd fastmcp-server.git

# Remove files from history
java -jar bfg.jar --delete-files OAUTH_COMPLETE.md
java -jar bfg.jar --delete-files SERVER_OAUTH_COMPLETE.md

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: This rewrites history!)
git push --force
```

**Option B: Using git filter-repo (Alternative)**

```bash
# Install git-filter-repo
pip install git-filter-repo

# Backup first
cd ..
cp -r fastmcp-server fastmcp-server-backup
cd fastmcp-server

# Remove files from entire history
git filter-repo --path OAUTH_COMPLETE.md --invert-paths
git filter-repo --path SERVER_OAUTH_COMPLETE.md --invert-paths

# Force push
git push origin main --force
```

**Option C: Nuclear Option - Start Fresh Repository**

If the credentials were exposed in multiple commits:

```bash
# 1. Create new empty repo on GitHub (different name)
# 2. Copy only current working files to new directory
# 3. Initialize new git repo
# 4. Push to new repository
# 5. Archive old repository (don't delete - needed for audit)
```

---

### 3. Verify .gitignore

Check that sensitive files are properly ignored:

```bash
# Verify .env is gitignored
git check-ignore .env
# Should output: .env

# Check for any sensitive files tracked
git ls-files | grep -E '\.env$|secret|key|credential'
```

---

### 4. Update All Deployed Instances

After rotating credentials:

**Docker:**
```bash
docker compose down
# Update docker-compose.yml or .env with new credentials
docker compose up --build -d
```

**Local:**
```bash
# Kill running server
# Update .env file
python -m src.server_oauth
```

---

### 5. GitHub Security Settings

1. Go to: https://github.com/ShashankShekhar00/fastmcp-server/settings/secrets
2. Add secrets as GitHub Actions secrets (if using CI/CD)
3. Never commit `.env` files
4. Use environment variables in production

---

### 6. Monitor for Unauthorized Access

**Auth0 Dashboard:**
- Check Logs → Recent activity
- Look for unexpected authentication attempts
- Review active sessions

**OpenWeatherMap:**
- Check API usage
- Look for unusual spikes

---

## Prevention Checklist

- [ ] Rotated Auth0 Client Secret
- [ ] Rotated OpenWeatherMap API Key
- [ ] Updated local `.env` with new credentials
- [ ] Cleaned git history (chose option A, B, or C)
- [ ] Verified `.gitignore` includes `.env`
- [ ] Restarted all deployed instances
- [ ] Confirmed no `.env` in `git ls-files`
- [ ] Set up GitHub secret scanning alerts
- [ ] Documented incident in security log

---

## GitHub Secret Scanning

Enable GitHub's secret scanning:
1. Repository Settings → Security & Analysis
2. Enable "Secret scanning"
3. Enable "Push protection"

This will prevent future accidental commits of secrets.

---

## Current Status

- **Date**: November 27, 2025
- **Alert**: GitGuardian detected Auth0 keys
- **Files**: OAUTH_COMPLETE.md, SERVER_OAUTH_COMPLETE.md (deleted but in history)
- **Action Required**: Rotate credentials + clean history

---

## Contact

If credentials were used maliciously, contact:
- Auth0 Support: https://support.auth0.com/
- OpenWeatherMap Support: https://home.openweathermap.org/questions

---

**CRITICAL: Do not proceed with development until credentials are rotated!**
