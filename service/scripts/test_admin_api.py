import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8765"

def test_admin_api():
    print("Testing /admin UI access...")
    req = urllib.request.Request(f"{BASE_URL}/admin")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        html = res.read().decode("utf-8")
        assert "Documents" in html
        assert "Admin" in html
        print("[PASS] /admin page served correctly.")

    print("\nTesting /api/admin/login with incorrect password...")
    payload = json.dumps({"password": "wrongpassword"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "Should have failed with 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print("[PASS] Blocked unauthorized login accurately.")

    print("\nTesting /api/admin/login with correct password...")
    payload = json.dumps({"password": "admin123"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        assert data.get("ok") is True
        token = data.get("token")
        assert token and len(token) >= 16
        print(f"[PASS] Successfully authenticated. Token: {token[:8]}...")

    print("\nTesting /api/admin/config retrieval with session token...")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/config", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        config = json.loads(res.read().decode("utf-8"))
        assert config.get("ok") is True
        print(f"[PASS] Retrieved active config: model={config.get('model')}, groq_key_set={config.get('groq_api_key_set')}")

    print("\nTesting /api/admin/config update...")
    update_payload = json.dumps({
        "groq_api_key": "gsk_test1234567890abcdefghijklmnopqrstuvwxyz",
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/config",
        data=update_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as res:
        update_res = json.loads(res.read().decode("utf-8"))
        assert update_res.get("ok") is True
        print(f"[PASS] Successfully updated settings: {update_res.get('message')}")

    print("\nRe-verifying config after update...")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/config", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        config2 = json.loads(res.read().decode("utf-8"))
        assert config2.get("groq_api_key_set") is True
        assert config2.get("groq_api_key_masked").startswith("gsk_")
        print(f"[PASS] Active key verified: {config2.get('groq_api_key_masked')}")

    print("\n==========================================")
    print("ALL ADMIN SYSTEM TESTS PASSED CLEANLY!")
    print("==========================================")

if __name__ == "__main__":
    test_admin_api()
