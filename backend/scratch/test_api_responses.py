import requests

headers = {
    "Authorization": "Bearer mock-token",
    "Content-Type": "application/json"
}

payload = {
    "job_id": "test_id",
    "job_title": "Python Developer",
    "company": "Citi",
    "jd_text": "We are looking for a Python developer with experience in FastAPI."
}

print("--- Testing Cover Letter Generate ---")
res_cl = requests.post("http://127.0.0.1:8000/api/cover-letter/generate", json=payload, headers=headers)
print("Status:", res_cl.status_code)
try:
    print("Response JSON:", res_cl.json())
except Exception as e:
    print("Failed to decode JSON:", e)
    print("Text:", res_cl.text[:500])

print("\n--- Testing Resume PDF Generate ---")
res_pdf = requests.post("http://127.0.0.1:8000/api/resume/generate-pdf", json=payload, headers=headers)
print("Status:", res_pdf.status_code)
try:
    print("Response Content-Type:", res_pdf.headers.get("Content-Type"))
    print("Content Length:", len(res_pdf.content))
    if "application/json" in res_pdf.headers.get("Content-Type", ""):
        print("Response JSON:", res_pdf.json())
    else:
        print("Start of binary content:", res_pdf.content[:50])
except Exception as e:
    print("Error:", e)
