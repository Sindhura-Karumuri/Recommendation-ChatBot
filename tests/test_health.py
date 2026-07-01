import os
import urllib.request
import json

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")


def test_health():
    r = urllib.request.urlopen(f"{BASE_URL}/health", timeout=10)
    data = json.loads(r.read())
    assert data == {"status": "ok"}, f"Unexpected: {data}"
    print("PASS test_health")


if __name__ == "__main__":
    test_health()
