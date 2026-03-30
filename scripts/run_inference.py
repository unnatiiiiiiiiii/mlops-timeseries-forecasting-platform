import requests

payload = {
    "latest_values": [
        122.1, 123.3, 120.2, 121.8, 124.4, 128.2, 126.9, 127.3, 129.6, 130.1,
        131.7, 132.5, 133.8, 131.1, 130.9, 132.3, 134.2, 136.4, 137.1, 138.2,
        137.3, 139.5, 140.1, 141.0, 142.8, 143.9, 145.3, 146.0, 147.1, 148.8,
    ]
}

resp = requests.post("http://localhost:8000/predict/realtime", json=payload, timeout=30)
print(resp.status_code)
print(resp.json())
