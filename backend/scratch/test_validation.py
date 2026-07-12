import requests

# Set mock Authorization token
headers = {
    "Authorization": "Bearer mock-token-123",
    "Content-Type": "application/json"
}

# Construct the payload similar to what the frontend sends
payload = {
    "job_id": "test_id",
    "job_title": "Python Developer",
    "company": "Test Company",
    "jd_text": "We are looking for a Python developer with experience in FastAPI."
}

# Test cover letter generation
res = requests.post("http://127.0.0.1:8000/api/cover-letter/generate", json=payload, headers=headers)
print("Response Status Code:", res.status_code)
print("Response JSON:")
print(res.json())
