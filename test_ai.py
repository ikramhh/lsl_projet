import requests
import json

# Test AI Service directly
url = "http://localhost:8002/predict/"
data = {"image": "test_base64_string"}

print("Testing AI Service directly...")
print(f"POST {url}")

response = requests.post(url, json=data)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
