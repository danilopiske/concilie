import requests
import sys

try:
    print("Requesting /processamentos/...")
    response = requests.get("http://127.0.0.1:8000/api/v1/processamentos/")
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print("Error Text:", response.text)
    else:
        print("Success!")
        print("Data sample:", response.json()[:2])
except Exception as e:
    print(f"Exception: {e}")
