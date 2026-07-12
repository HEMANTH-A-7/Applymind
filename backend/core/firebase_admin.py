"""
Firebase Admin SDK — server-side only.
Validates Firebase ID tokens, writes to Firestore via Admin SDK
(bypasses Security Rules — controlled server access).

NEVER import this in frontend code.
Requires FIREBASE_SERVICE_ACCOUNT_JSON env var (JSON string of service account).
"""
import os
import json
import logging
from datetime import datetime
from functools import lru_cache
from typing import Optional

import firebase_admin
from firebase_admin import credentials, auth as fb_auth, firestore
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ─── Initialise Firebase Admin (singleton) ────────────────────────────
@lru_cache(maxsize=1)
def get_firebase_app() -> firebase_admin.App:
    """Initialise once, reuse forever."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        sa_dict = json.loads(sa_json)
        cred = credentials.Certificate(sa_dict)
    else:
        # Local dev fallback: use service account file
        sa_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-service-account.json")
        if os.path.exists(sa_path):
            cred = credentials.Certificate(sa_path)
        else:
            logger.warning("No Firebase credentials found — using mock auth for dev")
            return None  # type: ignore

    return firebase_admin.initialize_app(cred)


@lru_cache(maxsize=1)
def get_firestore_client():
    """Return Firestore client. Call after get_firebase_app()."""
    get_firebase_app()
    return firestore.client()


# ─── Token verification ────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    cred: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """
    FastAPI dependency — validates Firebase ID token from Authorization header.
    Returns decoded token dict with uid, email, etc.

    Usage:
        @router.get("/protected")
        async def endpoint(token: dict = Depends(verify_firebase_token)):
            user_id = token["uid"]
    """
    app = get_firebase_app()

    # Dev mode: no Firebase configured
    if app is None:
        logger.debug("Firebase not configured — returning mock user for dev")
        return {"uid": "dev-user-123", "email": "dev@applymind.ai", "name": "Dev User"}

    if not cred or not cred.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization token")

    try:
        decoded = fb_auth.verify_id_token(
            cred.credentials,
            check_revoked=True,
            clock_skew_seconds=60,
        )
        return decoded
    except fb_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Token has been revoked — sign in again")
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired — refresh and retry")
    except fb_auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# Optional: no-error version (for endpoints that work with or without auth)
async def optional_firebase_token(
    cred: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[dict]:
    try:
        return await verify_firebase_token(cred)
    except HTTPException:
        return None


# ─── Firestore helpers ────────────────────────────────────────────────
# ─── Firestore helpers ────────────────────────────────────────────────
class FirestoreDB:
    """Thin wrapper around Firestore client for common ApplyMind patterns."""

    def __init__(self):
        self.db = get_firestore_client()

    # ── Users ──────────────────────────────────────────────────────────
    def get_user(self, uid: str) -> Optional[dict]:
        doc = self.db.collection("users").document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            if data and data.get("deletedAt") is None:
                return data
        return None

    def update_user(self, uid: str, data: dict):
        self.db.collection("users").document(uid).set({
            **data,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }, merge=True)

    # ── Resumes ────────────────────────────────────────────────────────
    def save_resume(self, uid: str, resume_data: dict) -> str:
        ref = self.db.collection("users").document(uid) \
                     .collection("resumes").document()
        ref.set({
            **resume_data,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "createdBy": uid,
            "updatedBy": uid,
            "savedAt": firestore.SERVER_TIMESTAMP,
            "deletedAt": None
        })
        return ref.id

    def get_latest_resume(self, uid: str) -> Optional[dict]:
        docs = (
            self.db.collection("users").document(uid)
                   .collection("resumes")
                   .order_by("savedAt", direction=firestore.Query.DESCENDING)
                   .stream()
        )
        for doc in docs:
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                return {**data, "id": doc.id}
        return None

    def soft_delete_resume(self, uid: str, resume_id: str) -> bool:
        doc_ref = self.db.collection("users").document(uid).collection("resumes").document(resume_id)
        if doc_ref.get().exists:
            doc_ref.update({
                "deletedAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "updatedBy": uid
            })
            return True
        return False

    # ── Jobs ───────────────────────────────────────────────────────────
    def save_jobs(self, uid: str, jobs: list[dict]):
        batch = self.db.batch()
        col = self.db.collection("users").document(uid).collection("jobs")
        for job in jobs:
            ref = col.document(job.get("job_id", col.document().id))
            batch.set(ref, {
                **job,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "createdBy": uid,
                "updatedBy": uid,
                "savedAt": firestore.SERVER_TIMESTAMP,
                "deletedAt": None
            })
        batch.commit()

    def get_jobs(self, uid: str, min_score: int = 0, limit: int = 50) -> list[dict]:
        query = (
            self.db.collection("users").document(uid)
                   .collection("jobs")
                   .where("fit_score", ">=", min_score)
                   .order_by("fit_score", direction=firestore.Query.DESCENDING)
                   .limit(limit)
        )
        results = []
        for doc in query.stream():
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append({**data, "id": doc.id})
        return results

    # ── Applications ───────────────────────────────────────────────────
    def log_application(self, uid: str, app_data: dict) -> str:
        ref = self.db.collection("users").document(uid) \
                     .collection("applications").document()
        ref.set({
            **app_data,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "createdBy": uid,
            "updatedBy": uid,
            "loggedAt": firestore.SERVER_TIMESTAMP,
            "deletedAt": None
        })
        # Update user counters
        self.db.collection("users").document(uid).update({
            "totalApplications": firestore.Increment(1),
            "applicationsThisWeek": firestore.Increment(1),
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "updatedBy": uid
        })
        return ref.id

    def get_applications(self, uid: str, limit: int = 50) -> list[dict]:
        docs = (
            self.db.collection("users").document(uid)
                   .collection("applications")
                   .order_by("loggedAt", direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .stream()
        )
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append({**data, "id": doc.id})
        return results

    def soft_delete_application(self, uid: str, app_id: str) -> bool:
        doc_ref = self.db.collection("users").document(uid).collection("applications").document(app_id)
        if doc_ref.get().exists:
            doc_ref.update({
                "deletedAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "updatedBy": uid
            })
            return True
        return False

    # ── Reports ────────────────────────────────────────────────────────
    def save_report(self, uid: str, report_type: str, content: dict):
        self.db.collection("users").document(uid) \
               .collection("reports").document(report_type) \
               .set({
                   **content,
                   "createdAt": firestore.SERVER_TIMESTAMP,
                   "updatedAt": firestore.SERVER_TIMESTAMP,
                   "createdBy": uid,
                   "updatedBy": uid,
                   "generatedAt": firestore.SERVER_TIMESTAMP,
                   "deletedAt": None
               }, merge=True)

    def get_report(self, uid: str, report_type: str) -> Optional[dict]:
        doc = self.db.collection("users").document(uid) \
                     .collection("reports").document(report_type).get()
        if doc.exists:
            data = doc.to_dict()
            if data and data.get("deletedAt") is None:
                return data
        return None

    # ── Admin Operations ───────────────────────────────────────────────
    def get_all_users(self) -> list[dict]:
        docs = self.db.collection("users").stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("deletedAt") is None:
                results.append({**data, "uid": doc.id})
        return results

    def update_user_plan(self, target_uid: str, plan: str, admin_uid: str):
        self.db.collection("users").document(target_uid).update({
            "plan": plan,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "updatedBy": admin_uid
        })

    def update_user_admin_status(self, target_uid: str, is_admin: bool, admin_uid: str):
        self.db.collection("users").document(target_uid).update({
            "isAdmin": is_admin,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "updatedBy": admin_uid
        })

    def log_audit_action(self, admin_uid: str, action: str, target_uid: str, details: dict):
        ref = self.db.collection("audit_logs").document()
        ref.set({
            "adminUid": admin_uid,
            "action": action,
            "targetUid": target_uid,
            "details": details,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

    def export_database_backup(self) -> dict:
        backup = {
            "exportedAt": datetime.utcnow().isoformat(),
            "users": [],
            "audit_logs": []
        }
        # Fetch users
        users = self.db.collection("users").stream()
        for u_doc in users:
            uid = u_doc.id
            u_data = u_doc.to_dict()
            
            # Subcollections
            resumes = [r.to_dict() for r in self.db.collection("users").document(uid).collection("resumes").stream()]
            jobs = [j.to_dict() for j in self.db.collection("users").document(uid).collection("jobs").stream()]
            applications = [a.to_dict() for a in self.db.collection("users").document(uid).collection("applications").stream()]
            reports = [rp.to_dict() for rp in self.db.collection("users").document(uid).collection("reports").stream()]
            
            backup["users"].append({
                "uid": uid,
                "profile": u_data,
                "resumes": resumes,
                "jobs": jobs,
                "applications": applications,
                "reports": reports
            })
        
        # Fetch audit logs
        audit_logs = self.db.collection("audit_logs").stream()
        for a_doc in audit_logs:
            backup["audit_logs"].append({
                "id": a_doc.id,
                **a_doc.to_dict()
            })
            
        return backup


# Singleton
_db_instance: Optional[FirestoreDB] = None

def get_db() -> FirestoreDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = FirestoreDB()
    return _db_instance
