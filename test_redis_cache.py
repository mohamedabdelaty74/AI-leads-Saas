"""
Redis Cache Performance Test
Tests the cache performance improvements by making repeated API calls
"""
import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/v1/auth/login"
CAMPAIGNS_ENDPOINT = f"{BASE_URL}/api/v1/campaigns"

# Test credentials (from .env defaults)
TEST_EMAIL = "admin@yourdomain.com"
TEST_PASSWORD = "change-this-secure-password-immediately"

def login():
    """Login and get access token"""
    print("[*] Logging in...")
    response = requests.post(LOGIN_ENDPOINT, json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("[OK] Login successful!")
        return token
    else:
        print(f"[ERROR] Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_cache_performance(token):
    """Test cache performance with multiple requests"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "="*60)
    print("REDIS CACHE PERFORMANCE TEST")
    print("="*60)

    # First request - Cache MISS (queries database)
    print("\n[1] First Request (Cache MISS - queries database)")
    start = time.time()
    response = requests.get(CAMPAIGNS_ENDPOINT, headers=headers)
    first_time = time.time() - start

    if response.status_code == 200:
        campaigns = response.json()
        print(f"   [OK] Success: {len(campaigns)} campaigns found")
        print(f"   [TIME] {first_time*1000:.2f}ms")
    else:
        print(f"   [ERROR] Failed: {response.status_code}")
        return

    # Second request - Cache HIT (from Redis)
    print("\n[2] Second Request (Cache HIT - from Redis)")
    start = time.time()
    response = requests.get(CAMPAIGNS_ENDPOINT, headers=headers)
    second_time = time.time() - start

    if response.status_code == 200:
        campaigns = response.json()
        print(f"   [OK] Success: {len(campaigns)} campaigns found")
        print(f"   [TIME] {second_time*1000:.2f}ms")
    else:
        print(f"   [ERROR] Failed: {response.status_code}")
        return

    # Multiple rapid requests to show cache performance
    print("\n[3] Multiple Rapid Requests (All from cache)")
    times = []
    for i in range(5):
        start = time.time()
        response = requests.get(CAMPAIGNS_ENDPOINT, headers=headers)
        times.append(time.time() - start)
        if response.status_code == 200:
            print(f"   Request {i+1}: {times[-1]*1000:.2f}ms [OK]")
        else:
            print(f"   Request {i+1}: Failed [ERROR]")

    # Calculate statistics
    avg_cache_time = sum(times) / len(times)
    speedup = first_time / avg_cache_time

    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"First Request (DB):      {first_time*1000:.2f}ms")
    print(f"Cached Requests (Avg):   {avg_cache_time*1000:.2f}ms")
    print(f"Speed Improvement:       {speedup:.1f}x faster!")
    print(f"Time Saved:              {(first_time - avg_cache_time)*1000:.2f}ms per request")
    print("="*60)

    if speedup > 2:
        print(f"\n[SUCCESS] Redis cache is {speedup:.1f}x faster than database queries!")
    else:
        print("\n[WARNING] Cache might not be working optimally")

def main():
    print("Starting Redis Cache Performance Test\n")

    # Login
    token = login()
    if not token:
        print("\n[ERROR] Cannot proceed without login token")
        print("[NOTE] Make sure backend is running and credentials are correct")
        return

    # Test cache performance
    test_cache_performance(token)

    print("\n[OK] Test complete!")

if __name__ == "__main__":
    main()
