import requests

BASE = "http://localhost:8000/api/v1"

# 1. Register
print("📝 Registering...")
r = requests.post(f"{BASE}/auth/register", json={"email": "test@example.com", "password": "pass123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✓ Registered. Token: {token[:20]}...")

# 2. Get profile
print("\n👤 Getting profile...")
r = requests.get(f"{BASE}/auth/me", headers=headers)
print(f"✓ Profile: {r.json()}")

# 3. Create bot
print("\n🤖 Creating bot...")
r = requests.post(f"{BASE}/bots/", json={"name": "My Bot", "strategy": "momentum", "config": {"symbol": "BTCUSDT"}}, headers=headers)
print(f"✓ Bot created: {r.json()}")

bot_id = r.json()["id"]

# 4. Start bot
print(f"\n▶ Starting bot {bot_id}...")
r = requests.post(f"{BASE}/bots/{bot_id}/start", headers=headers)
print(f"✓ {r.json()}")

# 5. List bots
print("\n📋 Listing bots...")
r = requests.get(f"{BASE}/bots/", headers=headers)
print(f"✓ Bots: {r.json()}")