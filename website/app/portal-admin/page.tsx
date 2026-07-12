"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { doc, getDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { authFetch, useAuth } from "@/lib/auth";
import ThemeToggle from "@/components/ThemeToggle";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UserProfile {
  uid: string;
  email: string;
  displayName?: string;
  plan: string;
  isAdmin?: boolean;
  createdAt?: any;
  totalApplications?: number;
}

export default function AdminPortal() {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();

  const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
  const [checkingAdmin, setCheckingAdmin] = useState(true);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [search, setSearch] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");
  const [exporting, setExporting] = useState(false);

  // ─── Verify Admin Status ───
  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }

    const checkAdminStatus = async () => {
      try {
        const userRef = doc(db, "users", user.uid);
        const snap = await getDoc(userRef);
        if (snap.exists() && snap.data()?.isAdmin === true) {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } catch (err) {
        console.error("Error checking admin privilege:", err);
        setIsAdmin(false);
      } finally {
        setCheckingAdmin(false);
      }
    };

    checkAdminStatus();
  }, [user, loading, router]);

  // ─── Fetch Users List ───
  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return;
    setLoadingUsers(true);
    try {
      const res = await authFetch(`${API}/api/admin/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
      } else {
        showStatus("Failed to retrieve user list from backend.", "error");
      }
    } catch {
      showStatus("Backend is offline.", "error");
    } finally {
      setLoadingUsers(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
    }
  }, [isAdmin, fetchUsers]);

  // ─── Toast Status Helpers ───
  const showStatus = (msg: string, type: "success" | "error") => {
    setStatusMsg(msg);
    setStatusType(type);
    setTimeout(() => {
      setStatusMsg("");
      setStatusType("");
    }, 4000);
  };

  // ─── Update Plan ───
  const handlePlanChange = async (targetUid: string, newPlan: string) => {
    try {
      const res = await authFetch(`${API}/api/admin/users/${targetUid}/plan`, {
        method: "POST",
        body: JSON.stringify({ plan: newPlan }),
      });
      if (res.ok) {
        showStatus(`Plan updated successfully for user ${targetUid}`, "success");
        fetchUsers();
      } else {
        const data = await res.json();
        showStatus(data.detail || "Failed to update plan.", "error");
      }
    } catch {
      showStatus("Error communicating with server.", "error");
    }
  };

  // ─── Toggle Admin Privilege ───
  const handleAdminToggle = async (targetUid: string, currentStatus: boolean) => {
    const confirmToggle = window.confirm(
      `Are you sure you want to ${currentStatus ? "revoke" : "grant"} Admin access for this user?`
    );
    if (!confirmToggle) return;

    try {
      const res = await authFetch(`${API}/api/admin/users/${targetUid}/admin`, {
        method: "POST",
        body: JSON.stringify({ is_admin: !currentStatus }),
      });
      if (res.ok) {
        showStatus(`Admin status updated for user ${targetUid}`, "success");
        fetchUsers();
      } else {
        const data = await res.json();
        showStatus(data.detail || "Failed to update admin status.", "error");
      }
    } catch {
      showStatus("Error communicating with server.", "error");
    }
  };

  // ─── Export JSON Database Backup ───
  const handleExportBackup = async () => {
    setExporting(true);
    try {
      const res = await authFetch(`${API}/api/admin/backup`);
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `applymind_db_backup_${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showStatus("Database backup downloaded successfully.", "success");
      } else {
        showStatus("Failed to generate database backup.", "error");
      }
    } catch {
      showStatus("Server error during backup generation.", "error");
    } finally {
      setExporting(false);
    }
  };

  // ─── Filter Users ───
  const filteredUsers = users.filter((u) => {
    const term = search.toLowerCase();
    return (
      u.email.toLowerCase().includes(term) ||
      (u.displayName && u.displayName.toLowerCase().includes(term)) ||
      u.uid.toLowerCase().includes(term)
    );
  });

  if (loading || checkingAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-3 h-3 rounded-full animate-ping bg-[#6C63FF]" />
      </div>
    );
  }

  if (isAdmin === false) {
    return (
      <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        <div className="max-w-md w-full glass-panel rounded-2xl p-8 border border-red-500/20 text-center space-y-6">
          <div className="text-5xl">🔒</div>
          <h1 className="text-2xl font-bold text-red-500">Access Denied</h1>
          <p className="text-white/60 text-sm leading-relaxed">
            This workspace area is restricted to system administrators. Unauthorized entry attempts are logged.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push("/dashboard")}
              className="px-6 py-2.5 rounded-xl font-bold text-sm bg-white text-black hover:scale-105 transition-all"
            >
              Dashboard
            </button>
            <button
              onClick={() => signOut()}
              className="px-6 py-2.5 rounded-xl font-bold text-sm border border-white/10 hover:bg-white/5 transition-all"
            >
              Sign Out
            </button>
          </div>
        </div>
        <style jsx global>{`
          .glass-panel { background: rgba(255,255,255,0.02); }
        `}</style>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
      {/* Header */}
      <header className="sticky top-0 z-20 bg-black/85 backdrop-blur-xl border-b border-white/5 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-[#6C63FF] font-bold text-2xl">⬢</span>
          <div>
            <h1 className="font-bold text-white text-lg tracking-tight">Admin Console</h1>
            <p className="text-white/30 text-xs mt-0.5">ApplyMind AI System Administration</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <button
            onClick={() => router.push("/dashboard")}
            className="text-xs px-4 py-2 rounded-xl border border-white/10 hover:border-[#6C63FF]/55 text-white/70 hover:text-white transition-all"
          >
            ← Application Dashboard
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Toast Notification */}
        {statusMsg && (
          <div
            className={`fixed top-6 right-6 z-50 px-5 py-3 rounded-xl border text-sm font-semibold shadow-2xl transition-all duration-300 animate-slide-in
              ${statusType === "success" ? "bg-[#00E5A0]/10 border-[#00E5A0]/30 text-[#00E5A0]" : "bg-red-500/10 border-red-500/30 text-red-400"}`}
          >
            {statusType === "success" ? "✓" : "⚠"} {statusMsg}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-panel rounded-2xl p-5 border border-white/5">
            <p className="text-[10px] text-white/40 uppercase tracking-widest">Total Accounts</p>
            <p className="font-bold text-3xl text-white mt-1">{users.length}</p>
            <p className="text-[10px] text-white/30 mt-1">Registered profiles</p>
          </div>
          <div className="glass-panel rounded-2xl p-5 border border-white/5">
            <p className="text-[10px] text-white/40 uppercase tracking-widest">Pro / Elite Users</p>
            <p className="font-bold text-3xl text-[#00D4FF] mt-1">
              {users.filter((u) => u.plan === "pro" || u.plan === "elite").length}
            </p>
            <p className="text-[10px] text-white/30 mt-1">Premium subscriptions</p>
          </div>
          <div className="glass-panel rounded-2xl p-5 border border-white/5">
            <p className="text-[10px] text-white/40 uppercase tracking-widest">System Admins</p>
            <p className="font-bold text-3xl text-[#6C63FF] mt-1">
              {users.filter((u) => u.isAdmin).length}
            </p>
            <p className="text-[10px] text-white/30 mt-1">Active console operators</p>
          </div>
          <div className="glass-panel rounded-2xl p-5 border border-[#6C63FF]/20 bg-[#6C63FF]/3 flex flex-col justify-between">
            <div>
              <p className="text-[10px] text-white/40 uppercase tracking-widest">System Backup</p>
              <p className="text-white/60 text-xs mt-1">Export full database snapshot</p>
            </div>
            <button
              onClick={handleExportBackup}
              disabled={exporting}
              className="mt-3 w-full py-2 bg-[#6C63FF] hover:bg-[#6c63ff]/80 disabled:bg-[#131929] disabled:text-white/30 rounded-xl font-bold text-xs text-black transition-all flex items-center justify-center gap-1.5"
            >
              {exporting ? "⏳ Exporting..." : "📥 Generate Snapshot"}
            </button>
          </div>
        </div>

        {/* User Management Section */}
        <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden">
          {/* Controls */}
          <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-4 bg-white/1">
            <div>
              <h2 className="font-bold text-white text-base">User Management</h2>
              <p className="text-white/40 text-xs mt-0.5">Search, adjust plans, or configure admin access levels</p>
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Search by name, email, or UID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-72 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-white/30 focus:outline-none focus:border-[#6C63FF]/55 transition-colors"
              />
              <button
                onClick={fetchUsers}
                disabled={loadingUsers}
                className="px-4 py-2.5 rounded-xl border border-white/10 hover:bg-white/5 text-xs font-semibold disabled:opacity-40 transition-colors"
              >
                {loadingUsers ? "Refreshing..." : "🔄"}
              </button>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="p-16 text-center text-white/30 text-xs">Loading user list...</div>
            ) : filteredUsers.length > 0 ? (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/5 bg-white/1 text-white/40 font-bold uppercase tracking-wider">
                    <th className="p-4">User Details</th>
                    <th className="p-4">User ID (UID)</th>
                    <th className="p-4">Subscription Plan</th>
                    <th className="p-4">Applications</th>
                    <th className="p-4">Security Role</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr key={u.uid} className="border-b border-white/5 hover:bg-white/1 transition-all">
                      <td className="p-4">
                        <div className="font-bold text-white text-sm">{u.displayName || "ApplyMind User"}</div>
                        <div className="text-white/40 text-xs mt-0.5">{u.email}</div>
                      </td>
                      <td className="p-4 font-mono text-white/50 text-[10px] select-all">{u.uid}</td>
                      <td className="p-4">
                        <select
                          value={u.plan}
                          onChange={(e) => handlePlanChange(u.uid, e.target.value)}
                          className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-white focus:outline-none focus:border-[#6C63FF]/55 cursor-pointer"
                        >
                          <option value="free" className="bg-black">Free</option>
                          <option value="pro" className="bg-black">Pro ($29/mo)</option>
                          <option value="elite" className="bg-black">Elite ($99/mo)</option>
                        </select>
                      </td>
                      <td className="p-4">
                        <span className="font-bold text-white">{u.totalApplications ?? 0}</span>
                        <span className="text-white/30 text-[10px] block">applications logged</span>
                      </td>
                      <td className="p-4">
                        <button
                          onClick={() => handleAdminToggle(u.uid, u.isAdmin || false)}
                          disabled={u.uid === user?.uid} // prevent self-revocation
                          className={`px-3 py-1.5 rounded-xl font-bold text-[10px] border transition-all
                            ${u.isAdmin
                              ? "bg-[#6C63FF]/15 border-[#6C63FF]/40 text-[#6C63FF] hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400"
                              : "bg-white/5 border-white/10 text-white/50 hover:bg-[#6C63FF]/15 hover:border-[#6C63FF]/30 hover:text-[#6C63FF]"
                            }`}
                        >
                          {u.isAdmin ? "★ System Admin" : "☆ Grant Admin"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-16 text-center text-white/30 text-xs">No user profiles matched your search term.</div>
            )}
          </div>
        </div>
      </main>

      <footer className="mt-auto py-6 border-t border-white/5 text-center text-[10px] text-white/20">
        ApplyMind AI Operations Portal · Confidential System Access Only
      </footer>

      <style jsx global>{`
        .glass-panel { background: rgba(255,255,255,0.02); }
        @keyframes slide-in {
          from { transform: translateX(100%) translateY(0); opacity: 0; }
          to { transform: translateX(0) translateY(0); opacity: 1; }
        }
        .animate-slide-in { animation: slide-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}</style>
    </div>
  );
}
