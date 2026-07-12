import sys
sys.path.insert(0, ".")
from core.firebase_admin import get_db

db = get_db()
# Let's query jobs for the dev user or any user in Firestore
users = db.get_all_users()
print("Registered Users:", [u.get("uid") for u in users])
if users:
    uid = users[0].get("uid")
    jobs = db.get_jobs(uid, min_score=0)
    print(f"Number of jobs for user {uid}: {len(jobs)}")
    if jobs:
        print("Keys of first job:", list(jobs[0].keys()))
        print("Job Title:", jobs[0].get("title"))
        print("Job Company:", jobs[0].get("company"))
        print("Job jd_text type:", type(jobs[0].get("jd_text")))
        print("Job jd_text length:", len(jobs[0].get("jd_text")) if jobs[0].get("jd_text") else "None/Empty")
