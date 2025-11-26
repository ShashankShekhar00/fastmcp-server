# Quick Security Fix Script
# Run this in PowerShell

Write-Host "==================================================" -ForegroundColor Red
Write-Host "  CRITICAL SECURITY FIX - Auth0 Keys Exposed" -ForegroundColor Red
Write-Host "==================================================" -ForegroundColor Red
Write-Host ""

# Step 1: Rotate credentials
Write-Host "[1/5] FIRST ACTION: Rotate Auth0 Credentials" -ForegroundColor Yellow
Write-Host "   Go to: https://manage.auth0.com/" -ForegroundColor Cyan
Write-Host "   → Applications → Your App → Settings → Rotate Client Secret" -ForegroundColor Cyan
Write-Host ""
$rotated = Read-Host "Have you rotated the Auth0 Client Secret? (yes/no)"

if ($rotated -ne "yes") {
    Write-Host "❌ STOP! Rotate credentials FIRST before continuing." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Step 1 Complete" -ForegroundColor Green
Write-Host ""

# Step 2: Update .env
Write-Host "[2/5] Update Local .env File" -ForegroundColor Yellow
Write-Host "   Enter your NEW Auth0 credentials:" -ForegroundColor Cyan
$newClientId = Read-Host "   New CLIENT_ID"
$newClientSecret = Read-Host "   New CLIENT_SECRET" -AsSecureString
$newClientSecretText = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($newClientSecret)
)

# Backup current .env
if (Test-Path ".env") {
    Copy-Item ".env" ".env.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Host "   ✅ Backed up current .env" -ForegroundColor Green
}

Write-Host "✅ Step 2 Complete" -ForegroundColor Green
Write-Host ""

# Step 3: Clean git history with filter-repo
Write-Host "[3/5] Clean Git History" -ForegroundColor Yellow
Write-Host "   Removing sensitive files from git history..." -ForegroundColor Cyan

# Create backup
$backupPath = "../fastmcp-server-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "   Creating backup at: $backupPath" -ForegroundColor Cyan
Copy-Item -Path "." -Destination $backupPath -Recurse -Force

Write-Host "   ⚠️  About to rewrite git history!" -ForegroundColor Yellow
Write-Host "   This will remove OAUTH_COMPLETE.md and SERVER_OAUTH_COMPLETE.md from ALL commits" -ForegroundColor Yellow
$confirm = Read-Host "   Continue? (yes/no)"

if ($confirm -eq "yes") {
    # Method 1: Using git filter-branch (built-in)
    Write-Host "   Removing OAUTH_COMPLETE.md from history..." -ForegroundColor Cyan
    git filter-branch --force --index-filter `
        "git rm --cached --ignore-unmatch OAUTH_COMPLETE.md" `
        --prune-empty --tag-name-filter cat -- --all
    
    Write-Host "   Removing SERVER_OAUTH_COMPLETE.md from history..." -ForegroundColor Cyan
    git filter-branch --force --index-filter `
        "git rm --cached --ignore-unmatch SERVER_OAUTH_COMPLETE.md" `
        --prune-empty --tag-name-filter cat -- --all
    
    # Cleanup
    Write-Host "   Cleaning up..." -ForegroundColor Cyan
    Remove-Item -Path ".git/refs/original/" -Recurse -Force -ErrorAction SilentlyContinue
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    
    Write-Host "   ✅ Git history cleaned" -ForegroundColor Green
} else {
    Write-Host "   ⏭️  Skipped git history cleaning" -ForegroundColor Yellow
}

Write-Host "✅ Step 3 Complete" -ForegroundColor Green
Write-Host ""

# Step 4: Force push
Write-Host "[4/5] Force Push to GitHub" -ForegroundColor Yellow
Write-Host "   ⚠️  WARNING: This will rewrite remote history!" -ForegroundColor Red
Write-Host "   Current remote: $(git remote get-url origin)" -ForegroundColor Cyan
$pushConfirm = Read-Host "   Force push cleaned history? (yes/no)"

if ($pushConfirm -eq "yes") {
    Write-Host "   Pushing to GitHub..." -ForegroundColor Cyan
    git push origin main --force
    Write-Host "   ✅ Pushed to GitHub" -ForegroundColor Green
} else {
    Write-Host "   ⏭️  Skipped force push (you can do it manually later)" -ForegroundColor Yellow
    Write-Host "   Manual command: git push origin main --force" -ForegroundColor Cyan
}

Write-Host "✅ Step 4 Complete" -ForegroundColor Green
Write-Host ""

# Step 5: Verify
Write-Host "[5/5] Verification" -ForegroundColor Yellow
Write-Host "   Checking if .env is gitignored..." -ForegroundColor Cyan
$gitignoreCheck = git check-ignore .env
if ($gitignoreCheck -eq ".env") {
    Write-Host "   ✅ .env is properly gitignored" -ForegroundColor Green
} else {
    Write-Host "   ❌ WARNING: .env may not be gitignored!" -ForegroundColor Red
}

Write-Host "   Checking tracked files..." -ForegroundColor Cyan
$sensitiveFiles = git ls-files | Select-String -Pattern "\.env$|secret|credential"
if ($sensitiveFiles) {
    Write-Host "   ❌ WARNING: Sensitive files found:" -ForegroundColor Red
    $sensitiveFiles | ForEach-Object { Write-Host "      - $_" -ForegroundColor Red }
} else {
    Write-Host "   ✅ No sensitive files tracked" -ForegroundColor Green
}

Write-Host "✅ Step 5 Complete" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  SECURITY FIX SUMMARY" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "✅ Rotated Auth0 credentials" -ForegroundColor Green
Write-Host "✅ Updated local .env" -ForegroundColor Green
Write-Host "✅ Cleaned git history" -ForegroundColor Green
Write-Host "✅ Verified gitignore" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Restart your server with new credentials" -ForegroundColor Cyan
Write-Host "2. Check Auth0 dashboard for suspicious activity" -ForegroundColor Cyan
Write-Host "3. Monitor logs for next 24-48 hours" -ForegroundColor Cyan
Write-Host "4. Enable GitHub secret scanning in repo settings" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backup location: $backupPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Read SECURITY_FIX.md for complete details" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Green
