"""
Quick OAuth Tools Demo

A simple demonstration showing how to use the OAuth-protected tools.
Run this while the server is running.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("🎯 Quick OAuth Tools Demo")
print("=" * 70)

# Step 1: Get OAuth token
print("\n1️⃣ Getting OAuth token...")
response = requests.get(f"{BASE_URL}/get-token")
token = response.json().get('access_token')
print(f"✅ Token: {token[:50]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 2: Create Profile
print("\n2️⃣ Creating user profile...")
response = requests.post(
    f"{BASE_URL}/api/profile",
    headers=headers,
    json={
        "action": "create",
        "name": "Test User",
        "bio": "Testing OAuth-protected tools"
    }
)
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 3: Create a Note
print("\n3️⃣ Creating a personal note...")
response = requests.post(
    f"{BASE_URL}/api/notes",
    headers=headers,
    json={
        "action": "create",
        "title": "My First Note",
        "content": "This is my private note!",
        "tags": ["test"]
    }
)
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 4: List Notes
print("\n4️⃣ Listing all notes...")
response = requests.post(
    f"{BASE_URL}/api/notes",
    headers=headers,
    json={"action": "list"}
)
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 70)
print("✅ Demo complete! Your OAuth-protected tools are working!")
print("=" * 70)
