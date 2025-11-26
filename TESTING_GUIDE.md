# How to Test Your OAuth-Protected Tools

## The Problem:
The server was crashing due to **emoji characters** in print statements that Windows PowerShell couldn't display. **This is now fixed!**

## Server is Running! ✓

You can see:
```
[AUTH] ENABLED
[DATABASE] CONNECTED
[SSE] ENABLED
```

---

## How to Test (3 Easy Methods)

### Method 1: Using PowerShell (Simplest)

Open a **NEW** PowerShell terminal and run these commands:

```powershell
# Test 1: Check if server is healthy
curl http://localhost:8000/health

# Test 2: Get an OAuth token
$response = Invoke-RestMethod -Uri "http://localhost:8000/get-token" -Method GET
$token = $response.access_token
Write-Host "Token: $token"

# Test 3: Create a user profile (OAuth protected!)
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    action = "create"
    name = "Test User"
    bio = "Testing my OAuth tools"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/profile" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Test 4: Get your profile
$body = @{ action = "get" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/profile" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Test 5: Create a note
$body = @{
    action = "create"
    title = "My First Note"
    content = "This is my private note!"
    tags = @("test", "personal")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/notes" `
    -Method POST `
    -Headers $headers `
    -Body $body

# Test 6: List all your notes
$body = @{ action = "list" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/notes" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

---

### Method 2: Using Python Script (Already Created!)

Open a NEW terminal and run:

```bash
python scripts/quick_demo.py
```

This will automatically:
1. Get an OAuth token
2. Create a profile
3. Create a note
4. List your notes

---

### Method 3: Using VS Code REST Client or Postman

1. **Get Token:**
   ```
   GET http://localhost:8000/get-token
   ```
   Copy the `access_token` from response

2. **Create Profile:**
   ```
   POST http://localhost:8000/api/profile
   Authorization: Bearer YOUR_TOKEN_HERE
   Content-Type: application/json

   {
     "action": "create",
     "name": "John Doe",
     "bio": "Developer"
   }
   ```

3. **Create Note:**
   ```
   POST http://localhost:8000/api/notes
   Authorization: Bearer YOUR_TOKEN_HERE
   Content-Type: application/json

   {
     "action": "create",
     "title": "Important Note",
     "content": "This is my private note",
     "tags": ["work", "important"]
   }
   ```

4. **List Notes:**
   ```
   POST http://localhost:8000/api/notes
   Authorization: Bearer YOUR_TOKEN_HERE
   Content-Type: application/json

   {
     "action": "list"
   }
   ```

---

## Quick Verification

### Test Health Endpoint (No Auth Required):
```powershell
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "auth_enabled": true,
  "streaming_enabled": true,
  "database": true,
  "tools": {
    "file_operations": true,
    "weather": true,
    "user_profile": true,
    "personal_notes": true
  }
}
```

---

## What Each Tool Does

### 1. Profile Tool (`/api/profile`)
**Actions:** get, create, update, delete

**Example - Create Profile:**
```json
{
  "action": "create",
  "name": "Alice Johnson",
  "bio": "Full-stack developer",
  "preferences": {
    "theme": "dark",
    "notifications": true
  }
}
```

**Example - Get Profile:**
```json
{
  "action": "get"
}
```

### 2. Notes Tool (`/api/notes`)
**Actions:** create, get, list, update, delete

**Example - Create Note:**
```json
{
  "action": "create",
  "title": "Shopping List",
  "content": "Milk, Eggs, Bread",
  "tags": ["personal", "shopping"],
  "is_pinned": false
}
```

**Example - List All Notes:**
```json
{
  "action": "list",
  "include_archived": false,
  "pinned_only": false
}
```

**Example - Update Note:**
```json
{
  "action": "update",
  "note_id": 1,
  "content": "Updated content",
  "is_pinned": true
}
```

---

## Why It Works Now

**The Issue:**
- Server was crashing with: `UnicodeEncodeError: 'charmap' codec can't encode character`
- Caused by emoji characters (🚀, 🔐, 💾) in print statements
- Windows PowerShell with default encoding (cp1252) can't display these

**The Fix:**
- Removed all emoji characters from server.py
- Replaced with ASCII-safe characters (*, -, >>, [])
- Server now starts successfully!

---

## Troubleshooting

### Server not responding?
```powershell
# Check if server is running
netstat -ano | findstr :8000

# Restart server
# Press Ctrl+C in server terminal, then:
python -m src.server
```

### "Connection refused" error?
- Make sure server is running (check terminal)
- Wait a few seconds after starting server

### Token invalid?
- Get a fresh token: `curl http://localhost:8000/get-token`
- Token expires after some time

---

## Database Location

Your data is stored in:
```
./mcp_server.db
```

To inspect:
```bash
sqlite3 mcp_server.db
.tables
SELECT * FROM user_profiles;
SELECT * FROM user_notes;
```

---

## Summary

✅ **Server is now running properly**
✅ **OAuth authentication is enabled**
✅ **Database is connected**
✅ **Two OAuth-protected tools available:**
   - Profile Management
   - Personal Notes

**Test them using any of the 3 methods above!**
