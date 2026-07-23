"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { authFetch, useAuth } from "@/lib/auth";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───
interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  source: string;
  apply_url: string;
  fit_score?: number;
  fit_label?: string;
  recommendation?: string;
  jd_text: string;
  tags?: string[];
  groq_enriched?: boolean;
}

interface DashboardStatus {
  backend: string;
  resume_loaded: boolean;
  jobs_scraped: number;
  applications_logged: number;
  users_registered: number;
  groq_model: string;
}

// ─── Colors ───
const STATUS_COLORS: Record<string, string> = {
  SUCCESS: "#CCFF00", CAPTCHA_REQUIRED: "#FF6B35",
  MANUAL_REQUIRED: "#00F0FF", RATE_LIMITED: "#FF00FF",
  FORM_ERROR: "#FF4757", PENDING: "#888",
};
const STATUS_LABELS: Record<string, string> = {
  SUCCESS: "Applied", CAPTCHA_REQUIRED: "CAPTCHA",
  MANUAL_REQUIRED: "Manual", RATE_LIMITED: "Rate Ltd",
  FORM_ERROR: "Error", PENDING: "Pending",
};
const REC_COLOR: Record<string, string> = {
  strong_apply: "#CCFF00", apply: "#00F0FF",
  apply_with_caution: "#FF6B35", skip: "#444",
};

const renderSalary = (val: any, fallback: string = "") => {
  if (!val) return fallback;
  if (typeof val === "object") {
    if (val.min !== undefined && val.max !== undefined) {
      return `$${Number(val.min).toLocaleString()} - $${Number(val.max).toLocaleString()}`;
    }
    return JSON.stringify(val);
  }
  return String(val);
};

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: "⬡" },
  { id: "jobs", label: "Job Queue", icon: "◎" },
  { id: "resume", label: "Resume", icon: "▣" },
  { id: "market", label: "Market Intel", icon: "◈" },
  { id: "applications", label: "Applications", icon: "◉" },
  { id: "agents", label: "Agents", icon: "◍" },
];

// ─── API helper ───
async function api<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const res = await authFetch(`${API}${path}`, opts);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// RESUME UPLOAD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function ResumePanel({ onParsed }: { onParsed?: (d: any) => void }) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await authFetch(`${API}/api/resume/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) {
        setResult({ error: data.detail || data.message || "Upload failed" });
      } else {
        setResult(data);
        onParsed?.(data);
      }
    } catch {
      setResult({ error: "Backend offline. Run: uvicorn api.main:app --reload --port 8000" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5">
      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300
          ${dragging ? "border-[#CCFF00] bg-[#CCFF00]/5" : "border-white/10 hover:border-[#CCFF00]/40"}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
        <div className="text-5xl mb-4">{busy ? "⏳" : "📄"}</div>
        <p className="font-bold text-white text-lg mb-1">
          {busy ? "Parsing with Groq AI…" : "Drop resume here"}
        </p>
        <p className="text-xs text-white/30">PDF · DOCX · TXT — Max 10MB</p>
        {dragging && <div className="absolute inset-0 rounded-2xl bg-[#CCFF00]/5 border-2 border-[#CCFF00]" />}
      </div>

      {result && (
        <div className={`rounded-xl p-5 border ${result.error ? "border-red-500/20 bg-red-500/5" : "border-[#CCFF00]/20 bg-[#CCFF00]/3"}`}>
          {result.error ? (
            <p className="text-xs text-red-400 font-mono">{result.error}</p>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-[#CCFF00] font-bold text-sm">✓ Resume parsed</span>
                <span className="text-xs text-white/40">by Groq llama-3.3-70b</span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Skills", val: result.skills_found },
                  { label: "Words", val: result.word_count },
                  { label: "ATS Issues", val: result.ats_issues?.length ?? 0 },
                ].map(({ label, val }) => (
                  <div key={label} className="bg-white/3 rounded-lg p-3 text-center">
                    <p className="text-[#CCFF00] font-bold text-xl">{val}</p>
                    <p className="text-white/40 text-[10px] uppercase tracking-widest">{label}</p>
                  </div>
                ))}
              </div>
              {result.parsed_data?.contact?.name && (
                <p className="text-xs text-white/60">Detected: <span className="text-white font-bold">{result.parsed_data.contact.name}</span></p>
              )}
              {result.ats_issues?.slice(0, 3).map((issue: string, i: number) => (
                <p key={i} className="text-xs text-orange-400">⚠ {issue}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// JOB QUEUE PANEL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Cookie Helper functions
const setCookie = (name: string, value: string) => {
  const secure = window.location.protocol === "https:" ? "Secure;" : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=2592000; SameSite=Lax; ${secure}`;
};

const getCookie = (name: string): string => {
  if (typeof window === "undefined") return "";
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : "";
};

const deleteCookie = (name: string) => {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
};

const getCredentialsFromCookies = () => {
  try {
    const consent = getCookie("applymind_creds_consent") === "true";
    if (!consent) return null;
    
    const liStr = getCookie("applymind_linkedin_creds");
    const wfStr = getCookie("applymind_wellfound_creds");
    
    return {
      linkedin: liStr ? JSON.parse(liStr) : null,
      wellfound: wfStr ? JSON.parse(wfStr) : null,
    };
  } catch (e) {
    console.error("Failed to parse credentials from cookies", e);
    return null;
  }
};

const saveCredentialsToCookies = (linkedin: any, wellfound: any, consent: boolean) => {
  if (consent) {
    setCookie("applymind_creds_consent", "true");
    if (linkedin) setCookie("applymind_linkedin_creds", JSON.stringify(linkedin));
    if (wellfound) setCookie("applymind_wellfound_creds", JSON.stringify(wellfound));
  } else {
    deleteCookie("applymind_creds_consent");
    deleteCookie("applymind_linkedin_creds");
    deleteCookie("applymind_wellfound_creds");
  }
};


function JobQueuePanel() {
  const [keywords, setKeywords] = useState("python developer, backend engineer");
  const [location, setLocation] = useState("Remote");
  const [scraping, setScraping] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [scrapeStatus, setScrapeStatus] = useState("");
  const [selected, setSelected] = useState<Job | null>(null);
  const [sortBy, setSortBy] = useState("date");

  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);

  const [showCredsModal, setShowCredsModal] = useState(false);
  const [liUser, setLiUser] = useState("");
  const [liPass, setLiPass] = useState("");
  const [wfUser, setWfUser] = useState("");
  const [wfPass, setWfPass] = useState("");
  const [wfToken, setWfToken] = useState("");
  const [consentChecked, setConsentChecked] = useState(false);

  useEffect(() => {
    const loadJobs = async () => {
      try {
        const matches = await api<any>(`/api/jobs/matches?min_score=0&limit=60&sort_by=${sortBy}`);
        if (matches?.matches) {
          setJobs(matches.matches);
        }
      } catch (e) {
        console.error("Failed to load jobs", e);
      }
    };
    loadJobs();
  }, [sortBy]);

  // Load from cookies on mount
  useEffect(() => {
    try {
      const consent = getCookie("applymind_creds_consent") === "true";
      setConsentChecked(consent);
      if (consent) {
        const liStr = getCookie("applymind_linkedin_creds");
        if (liStr) {
          const parsed = JSON.parse(liStr);
          setLiUser(parsed.username || "");
          setLiPass(parsed.password || "");
        }
        const wfStr = getCookie("applymind_wellfound_creds");
        if (wfStr) {
          const parsed = JSON.parse(wfStr);
          setWfUser(parsed.username || "");
          setWfPass(parsed.password || "");
          setWfToken(parsed.oauth_token || "");
        }
      }
    } catch (e) {
      console.error("Failed to load credentials from cookies on mount", e);
    }
  }, []);

  const triggerScrape = async () => {
    setScraping(true);
    setScrapeStatus("Queuing scrape across LinkedIn + Remotive + Arbeitnow + Jobicy + The Muse + RemoteOK + HN + Web Search + Adzuna…");
    const kw = keywords.split(",").map(k => k.trim()).filter(Boolean);
    const res = await authFetch(`${API}/api/jobs/scrape`, {
      method: "POST",
      body: JSON.stringify({ keywords: kw, location, platforms: ["linkedin", "remotive", "arbeitnow", "jobicy", "themuse", "remoteok", "hn", "search_engine", "adzuna"], max_jobs: 60, sort_by: sortBy, country: "in" }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setScrapeStatus(data.detail || "Scrape failed to start");
      setScraping(false);
      return;
    }
    setScrapeStatus("Scraping in background… Fetching matches in 10s");
    await new Promise(r => setTimeout(r, 10000));
    const matches = await api<any>(`/api/jobs/matches?min_score=0&limit=60&sort_by=${sortBy}`);
    if (matches?.matches) {
      setJobs(matches.matches);
      setScrapeStatus(`Found ${matches.total} jobs · ${matches.apply_queue_count} ready to apply`);
    } else {
      setScrapeStatus("No matches yet — backend may still be scraping");
    }
    setScraping(false);
  };

  const handleDownloadResume = async (job: Job) => {
    setBusyAction("resume");
    try {
      const res = await authFetch(`${API}/api/resume/generate-pdf`, {
        method: "POST",
        body: JSON.stringify({
          job_id: job.job_id,
          job_title: job.title,
          company: job.company,
          jd_text: job.jd_text,
        }),
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `resume_${job.company.replace(/\s+/g, "_")}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const detail = await res.json().then(d => d?.detail).catch(() => null);
        alert(detail ? `Failed to generate tailored resume: ${detail}` : "Failed to generate PDF. Make sure reportlab is installed on the backend.");
      }
    } catch {
      alert("Error generating PDF.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleGenerateCoverLetter = async (job: Job) => {
    setBusyAction("cover");
    try {
      const res = await authFetch(`${API}/api/cover-letter/generate`, {
        method: "POST",
        body: JSON.stringify({
          job_id: job.job_id,
          job_title: job.title,
          company: job.company,
          jd_text: job.jd_text,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCoverLetter(data.cover_letter || data.cover_letter_text || data.text || "No text returned.");
      } else {
        const detail = await res.json().then(d => d?.detail).catch(() => null);
        alert(detail ? `Failed to generate cover letter: ${detail}` : "Failed to generate cover letter.");
      }
    } catch {
      alert("Error communicating with backend.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleAutoApply = async (job: Job) => {
    const consent = getCookie("applymind_creds_consent") === "true";
    if (!consent) {
      alert("Please configure your credentials and accept the Privacy Policy consent in the 'Platform Credentials' settings first.");
      setShowCredsModal(true);
      return;
    }
    const creds = getCredentialsFromCookies();

    setBusyAction("apply");
    try {
      const res = await authFetch(`${API}/api/apply/${job.job_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          credentials: creds
        }),
      });
      const data = await res.json();
      if (res.ok) {
        alert("✓ Application submitted successfully!");
      } else {
        alert(`⚠ Application failed: ${data.detail || "Submission error"}`);
      }
    } catch {
      alert("Error communicating with backend.");
    } finally {
      setBusyAction(null);
    }
  };

  const scoreColor = (s: number) =>
    s >= 80 ? "#CCFF00" : s >= 65 ? "#00F0FF" : s >= 45 ? "#FF6B35" : "#555";

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="glass-panel rounded-2xl p-5 border border-white/5">
        <p className="text-[10px] text-white/40 uppercase tracking-widest mb-4">Configure Scrape</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
            placeholder="Keywords (comma separated)"
            value={keywords}
            onChange={e => setKeywords(e.target.value)}
          />
          <input
            className="w-40 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
            placeholder="Location"
            value={location}
            onChange={e => setLocation(e.target.value)}
          />
          <button
            onClick={triggerScrape}
            disabled={scraping}
            className="px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 disabled:opacity-40"
            style={{ background: scraping ? "#1a1a1a" : "#CCFF00", color: "#000" }}
          >
            {scraping ? "Scraping…" : "⚡ Scrape Now"}
          </button>
          <button
            onClick={() => setShowCredsModal(true)}
            className="px-6 py-3 rounded-xl font-bold text-sm border border-white/10 hover:border-[#CCFF00]/40 hover:bg-white/3 text-white transition-all duration-200"
          >
            🔑 Platform Credentials
          </button>
        </div>
        {scrapeStatus && <p className="text-xs text-[#00F0FF] mt-3">{scrapeStatus}</p>}
      </div>

      {/* Job list + detail side-by-side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* List */}
        <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden">
          <div className="p-4 border-b border-white/5 flex justify-between items-center">
            <p className="text-[10px] text-white/40 uppercase tracking-widest">
              {jobs.length > 0 ? `${jobs.length} Jobs Found` : "No jobs yet — click Scrape Now"}
            </p>
            <div className="flex items-center gap-2">
              <label className="text-[10px] text-white/40 uppercase">Sort By:</label>
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
                className="bg-black border border-white/10 rounded-lg text-xs text-white px-2 py-1 focus:outline-none focus:border-[#CCFF00]/40"
              >
                <option value="date" className="bg-black text-white">Time Listed (Date)</option>
                <option value="score" className="bg-black text-white">Relevance (Score)</option>
              </select>
            </div>
          </div>
          <div className="overflow-y-auto max-h-[500px]">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                onClick={() => setSelected(job)}
                className={`p-4 border-b border-white/5 cursor-pointer transition-all duration-200 hover:bg-white/3
                  ${selected?.job_id === job.job_id ? "bg-[#CCFF00]/5 border-l-2 border-[#CCFF00]" : ""}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-white text-sm truncate">{job.title}</p>
                    <p className="text-white/50 text-xs truncate">{job.company} · {job.location}</p>
                    {job.salary && <p className="text-[#CCFF00] text-xs mt-0.5">{renderSalary(job.salary)}</p>}
                  </div>
                  {job.fit_score !== undefined && (
                    <div className="flex flex-col items-end shrink-0">
                      <span className="text-sm font-bold" style={{ color: scoreColor(job.fit_score) }}>
                        {job.fit_score}
                      </span>
                      <span className="text-[9px] text-white/30">{job.source}</span>
                    </div>
                  )}
                </div>
                <div className="flex gap-1.5 mt-2 flex-wrap">
                  {job.tags?.slice(0, 4).map(t => (
                    <span key={t} className="px-2 py-0.5 rounded-full bg-white/5 text-white/40 text-[10px]">{t}</span>
                  ))}
                  {job.groq_enriched && (
                    <span className="px-2 py-0.5 rounded-full bg-[#CCFF00]/10 text-[#CCFF00] text-[10px]">AI enriched</span>
                  )}
                </div>
              </div>
            ))}
            {jobs.length === 0 && (
              <div className="p-8 text-center text-white/20 text-sm">
                Jobs will appear here after scraping
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="glass-panel rounded-2xl border border-white/5 p-5">
          {selected ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-white text-lg">{selected.title}</h3>
                <p className="text-[#00F0FF] text-sm">{selected.company}</p>
                <p className="text-white/40 text-xs mt-1">{selected.location}</p>
              </div>
              {selected.fit_score !== undefined && (
                <div className="flex gap-3">
                  <div className="glass-panel rounded-xl p-3 text-center flex-1 border border-white/5">
                    <p className="font-bold text-xl" style={{ color: scoreColor(selected.fit_score) }}>
                      {selected.fit_score}
                    </p>
                    <p className="text-white/30 text-[10px]">Fit Score</p>
                  </div>
                  <div className="glass-panel rounded-xl p-3 text-center flex-1 border border-white/5">
                    <p className="font-bold text-sm" style={{ color: REC_COLOR[selected.recommendation ?? ""] ?? "#888" }}>
                      {selected.fit_label ?? "—"}
                    </p>
                    <p className="text-white/30 text-[10px]">Match</p>
                  </div>
                </div>
              )}
              <div className="bg-white/3 rounded-xl p-4">
                <p className="text-[10px] text-white/40 uppercase tracking-widest mb-2">Job Description</p>
                <p className="text-white/70 text-xs leading-relaxed line-clamp-10">{selected.jd_text || "No description available"}</p>
              </div>

              {/* Agentic AI Tools */}
              <div className="border-t border-white/5 pt-4 space-y-3">
                <p className="text-[10px] text-white/40 uppercase tracking-widest">Agentic AI Tools</p>
                
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleDownloadResume(selected)}
                    disabled={busyAction !== null}
                    className="py-2.5 rounded-xl border border-white/10 hover:border-[#CCFF00]/40 hover:bg-white/3 text-xs font-semibold text-white/80 hover:text-white transition-all disabled:opacity-40"
                  >
                    {busyAction === "resume" ? "⏳ Tailoring..." : "📄 Tailored Resume (PDF)"}
                  </button>
                  <button
                    onClick={() => handleGenerateCoverLetter(selected)}
                    disabled={busyAction !== null}
                    className="py-2.5 rounded-xl border border-white/10 hover:border-[#CCFF00]/40 hover:bg-white/3 text-xs font-semibold text-white/80 hover:text-white transition-all disabled:opacity-40"
                  >
                    {busyAction === "cover" ? "⏳ Writing..." : "✍ Tailored Cover Letter"}
                  </button>
                </div>

                <button
                  onClick={() => handleAutoApply(selected)}
                  disabled={busyAction !== null}
                  className="w-full py-3 rounded-xl font-bold text-xs bg-[#CCFF00] hover:bg-[#CCFF00]/90 text-black transition-all flex items-center justify-center gap-1.5 disabled:opacity-40"
                >
                  {busyAction === "apply" ? (
                    <>⏳ Submitting Application...</>
                  ) : (
                    <>⚡ Auto-Apply (Selenium submission)</>
                  )}
                </button>
              </div>

              <a
                href={selected.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center py-2.5 rounded-xl border border-white/10 hover:bg-white/3 text-xs font-semibold text-white/60 hover:text-white transition-all"
              >
                Open External Apply Link →
              </a>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-white/20 text-sm">
              Select a job to view details
            </div>
          )}
        </div>
      </div>

      {/* Cover Letter Modal */}
      {coverLetter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm">
          <div className="glass-panel max-w-2xl w-full rounded-2xl p-6 border border-white/10 bg-[#050505] space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-bold text-white text-base">Tailored Cover Letter</h3>
              <button onClick={() => setCoverLetter(null)} className="text-white/40 hover:text-white text-sm">✕</button>
            </div>
            <textarea
              readOnly
              className="w-full h-80 bg-white/5 border border-white/10 rounded-xl p-4 text-xs font-mono text-white/80 focus:outline-none focus:border-[#CCFF00]/40"
              value={coverLetter}
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(coverLetter);
                  alert("Cover letter copied to clipboard!");
                }}
                className="px-4 py-2 bg-[#CCFF00] text-black font-bold rounded-xl text-xs hover:scale-105 transition-all"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={() => setCoverLetter(null)}
                className="px-4 py-2 border border-white/10 hover:bg-white/5 rounded-xl text-xs text-white transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Platform Credentials Modal */}
      {showCredsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm">
          <div className="glass-panel max-w-lg w-full rounded-2xl p-6 border border-white/10 bg-[#050505] space-y-6">
            <div className="flex justify-between items-center border-b border-white/5 pb-4">
              <div className="flex items-center gap-2">
                <span className="text-[#CCFF00] text-lg">🔑</span>
                <h3 className="font-bold text-white text-base">Platform Credentials</h3>
              </div>
              <button onClick={() => setShowCredsModal(false)} className="text-white/40 hover:text-white text-sm">✕</button>
            </div>

            <p className="text-xs text-white/60 leading-relaxed">
              To automate job submissions via LinkedIn Easy Apply and Wellfound GraphQL, configure your credentials below. 
              <span className="text-[#00F0FF] font-semibold"> They are stored exclusively in your browser cookies</span> and are never persisted on our servers.
            </p>

            <div className="space-y-4">
              {/* LinkedIn Section */}
              <div className="space-y-3">
                <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">LinkedIn Account</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Email / Username"
                    value={liUser}
                    onChange={(e) => setLiUser(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
                  />
                  <input
                    type="password"
                    placeholder="Password"
                    value={liPass}
                    onChange={(e) => setLiPass(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
                  />
                </div>
              </div>

              {/* Wellfound Section */}
              <div className="space-y-3 pt-2">
                <p className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Wellfound Account (API/GraphQL)</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Email / Username (Optional)"
                    value={wfUser}
                    onChange={(e) => setWfUser(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
                  />
                  <input
                    type="password"
                    placeholder="Password (Optional)"
                    value={wfPass}
                    onChange={(e) => setWfPass(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
                  />
                </div>
                <input
                  type="password"
                  placeholder="Wellfound OAuth Token (Optional)"
                  value={wfToken}
                  onChange={(e) => setWfToken(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
                />
              </div>

              {/* Consent Checkbox */}
              <label className="flex items-start gap-3 cursor-pointer select-none pt-2">
                <input
                  type="checkbox"
                  checked={consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                  className="mt-0.5 accent-[#CCFF00] rounded"
                />
                <span className="text-[11px] text-white/60 leading-normal">
                  I consent to storing these credentials in my local browser cookies as outlined in the{" "}
                  <a href="/privacy" target="_blank" className="text-[#CCFF00] underline">
                    Privacy Policy
                  </a>
                  . I understand they are only sent to the server in-memory when I trigger auto-apply.
                </span>
              </label>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-white/5">
              <button
                onClick={() => {
                  saveCredentialsToCookies(null, null, false);
                  setLiUser("");
                  setLiPass("");
                  setWfUser("");
                  setWfPass("");
                  setWfToken("");
                  setConsentChecked(false);
                  alert("Platform credentials and consent cookies cleared.");
                  setShowCredsModal(false);
                }}
                className="px-4 py-2 border border-red-500/20 bg-red-500/5 text-red-400 font-bold rounded-xl text-xs hover:bg-red-500/10 transition-all"
              >
                Clear & Reset
              </button>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowCredsModal(false)}
                  className="px-4 py-2 border border-white/10 hover:bg-white/5 rounded-xl text-xs text-white transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (!consentChecked) {
                      alert("Please consent to the privacy policy storage checkbox to save.");
                      return;
                    }
                    const liCreds = liUser && liPass ? { username: liUser, password: liPass } : null;
                    const wfCreds = wfUser || wfPass || wfToken ? { username: wfUser, password: wfPass, oauth_token: wfToken } : null;
                    saveCredentialsToCookies(liCreds, wfCreds, true);
                    alert("✓ Credentials saved locally in cookies.");
                    setShowCredsModal(false);
                  }}
                  className="px-4 py-2 bg-[#CCFF00] text-black font-bold rounded-xl text-xs hover:scale-105 transition-all"
                >
                  Save Credentials
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MARKET INTEL PANEL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function MarketPanel() {
  const [role, setRole] = useState("python backend engineer");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);

  const fetchReport = async () => {
    setLoading(true);
    const data = await api<any>("/api/market/research", {
      method: "POST",
      body: JSON.stringify({ role, location: "Remote", skills: ["Python", "FastAPI"] }),
    });
    setReport(data);
    setLoading(false);
  };

  const renderMarketSalary = (val: any) => renderSalary(val, "—");

  return (
    <div className="space-y-5">
      <div className="glass-panel rounded-2xl p-5 border border-white/5 flex gap-3">
        <input
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#CCFF00]/40"
          value={role} onChange={e => setRole(e.target.value)}
          placeholder="Role (e.g. python backend engineer)"
        />
        <button
          onClick={fetchReport} disabled={loading}
          className="px-6 py-3 rounded-xl font-bold text-sm disabled:opacity-40"
          style={{ background: loading ? "#1a1a1a" : "#00F0FF", color: "#000" }}
        >
          {loading ? "Analyzing…" : "◈ Analyze"}
        </button>
      </div>

      {report && (
        <div className="space-y-4">
          {/* Salary */}
          {report.salary_data && (
            <div className="glass-panel rounded-2xl p-5 border border-white/5">
              <p className="text-[10px] text-white/40 uppercase tracking-widest mb-4">Salary Ranges (Groq Analysis)</p>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Junior", val: renderMarketSalary(report.salary_data.junior_level) },
                  { label: "Mid", val: renderMarketSalary(report.salary_data.mid_level) },
                  { label: "Senior", val: renderMarketSalary(report.salary_data.senior_level) },
                ].map(({ label, val }) => (
                  <div key={label} className="bg-white/3 rounded-xl p-4 text-center border border-white/5">
                    <p className="text-[#CCFF00] font-bold text-base">{val}</p>
                    <p className="text-white/40 text-[10px] uppercase tracking-widest mt-1">{label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills demand */}
          {report.skill_demand && (
            <div className="glass-panel rounded-2xl p-5 border border-white/5">
              <p className="text-[10px] text-white/40 uppercase tracking-widest mb-4">Skill Demand</p>
              <div className="space-y-3">
                {[
                  { label: "Must Have", skills: report.skill_demand.must_have ?? [], color: "#CCFF00" },
                  { label: "Nice to Have", skills: report.skill_demand.nice_to_have ?? [], color: "#00F0FF" },
                  { label: "Trending", skills: report.skill_demand.trending ?? [], color: "#FF00FF" },
                ].map(({ label, skills, color }) => (
                  <div key={label}>
                    <p className="text-[10px] mb-2" style={{ color }}>{label}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {(skills as string[]).map(s => (
                        <span key={s} className="px-2.5 py-1 rounded-full text-[10px] font-bold border"
                          style={{ borderColor: color + "44", color, background: color + "11" }}>{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          {report.market_summary && (
            <div className="glass-panel rounded-2xl p-5 border border-white/5">
              <p className="text-[10px] text-white/40 uppercase tracking-widest mb-3">AI Market Summary</p>
              <p className="text-white/70 text-sm leading-relaxed">{report.market_summary}</p>
            </div>
          )}
        </div>
      )}

      {!report && !loading && (
        <div className="glass-panel rounded-2xl p-10 text-center border border-white/5">
          <p className="text-white/20 text-sm">Click Analyze to generate Groq-powered market intelligence</p>
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// AGENTS PANEL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const AGENTS_META = [
  { id: "01", name: "Resume Intake", desc: "Parses PDF/DOCX → JSON via Groq", color: "#CCFF00" },
  { id: "02", name: "Market Research", desc: "Groq salary & skill demand analysis", color: "#00F0FF" },
  { id: "03", name: "Job Scraper", desc: "RemoteOK · HN Hiring · Indeed · BeautifulSoup", color: "#FF00FF" },
  { id: "04", name: "Match & Score", desc: "TF-IDF + Groq deep gap analysis", color: "#CCFF00" },
  { id: "05", name: "ATS Rewriter", desc: "Groq rewrites resume per JD keywords", color: "#00F0FF" },
  { id: "06", name: "Cover Letter", desc: "Groq A/B cover letters with tone matching", color: "#FF00FF" },
  { id: "07", name: "Credential Mgr", desc: "AES-256 encrypted credential vault", color: "#E0E0E0" },
  { id: "08", name: "Auto Submitter", desc: "Selenium · GraphQL · SMTP + Groq form answers", color: "#CCFF00" },
  { id: "09", name: "Analytics", desc: "IMAP inbox scan + Groq weekly report", color: "#00F0FF" },
];

function AgentsPanel({ backendOnline }: { backendOnline: boolean }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {AGENTS_META.map((agent) => (
        <div
          key={agent.id}
          className="glass-panel rounded-2xl p-5 border border-white/5 hover:border-[#CCFF00]/20 transition-all duration-300 group"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-white/30 bg-white/5 px-2 py-1 rounded-md">#{agent.id}</span>
              {backendOnline
                ? <span className="inline-block w-2 h-2 rounded-full bg-[#CCFF00] animate-pulse" />
                : <span className="inline-block w-2 h-2 rounded-full bg-white/20" />
              }
            </div>
          </div>
          <p className="font-bold text-white text-sm mb-1 group-hover:text-[#CCFF00] transition-colors">{agent.name}</p>
          <p className="text-white/40 text-xs leading-relaxed">{agent.desc}</p>
          <div className="mt-3 h-0.5 rounded-full w-0 group-hover:w-full transition-all duration-500"
            style={{ background: agent.color }} />
        </div>
      ))}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// OVERVIEW PANEL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const weeklyData = [
  { day: "Mon", applied: 32, responses: 4, interviews: 1 },
  { day: "Tue", applied: 45, responses: 7, interviews: 2 },
  { day: "Wed", applied: 28, responses: 3, interviews: 1 },
  { day: "Thu", applied: 50, responses: 9, interviews: 3 },
  { day: "Fri", applied: 41, responses: 6, interviews: 2 },
  { day: "Sat", applied: 20, responses: 2, interviews: 0 },
  { day: "Sun", applied: 15, responses: 2, interviews: 1 },
];

// Custom SVG Area Chart to avoid React 19 Recharts compatibility errors
function CustomAreaChart() {
  const data = weeklyData;
  const width = 600;
  const height = 180;
  const paddingLeft = 35;
  const paddingRight = 15;
  const paddingTop = 15;
  const paddingBottom = 25;
  
  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;
  
  const maxVal = 60;
  
  const getX = (index: number) => paddingLeft + (index * (chartWidth / (data.length - 1)));
  const getY = (val: number) => paddingTop + chartHeight - ((val / maxVal) * chartHeight);
  
  // Generate SVG path for 'applied'
  const appliedPath = `M ${getX(0)},${getY(data[0].applied)} ` + data.slice(1).map((d, i) => `L ${getX(i+1)},${getY(d.applied)}`).join(" ");
  const appliedAreaPath = `${appliedPath} L ${getX(data.length - 1)},${paddingTop + chartHeight} L ${getX(0)},${paddingTop + chartHeight} Z`;

  // Generate SVG path for 'responses'
  const responsesPath = `M ${getX(0)},${getY(data[0].responses)} ` + data.slice(1).map((d, i) => `L ${getX(i+1)},${getY(d.responses)}`).join(" ");
  const responsesAreaPath = `${responsesPath} L ${getX(data.length - 1)},${paddingTop + chartHeight} L ${getX(0)},${paddingTop + chartHeight} Z`;

  return (
    <div className="relative w-full h-[180px]">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%" className="overflow-visible">
        <defs>
          <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#CCFF00" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#CCFF00" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gR" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#00F0FF" stopOpacity={0} />
          </linearGradient>
        </defs>
        
        {/* Horizontal grid lines */}
        {[0, 20, 40, 60].map((val) => (
          <g key={val}>
            <line 
              x1={paddingLeft} 
              y1={getY(val)} 
              x2={width - paddingRight} 
              y2={getY(val)} 
              stroke="#ffffff08" 
              strokeDasharray="3 3" 
            />
            <text 
              x={paddingLeft - 8} 
              y={getY(val) + 3} 
              fill="#ffffff30" 
              fontSize={10} 
              textAnchor="end"
              className="font-mono"
            >
              {val}
            </text>
          </g>
        ))}

        {/* Areas */}
        <path d={appliedAreaPath} fill="url(#gA)" />
        <path d={responsesAreaPath} fill="url(#gR)" />

        {/* Lines */}
        <path d={appliedPath} fill="none" stroke="#CCFF00" strokeWidth={2} />
        <path d={responsesPath} fill="none" stroke="#00F0FF" strokeWidth={2} />

        {/* Grid vertical lines / labels */}
        {data.map((d, i) => (
          <g key={i}>
            <line 
              x1={getX(i)} 
              y1={paddingTop} 
              x2={getX(i)} 
              y2={paddingTop + chartHeight} 
              stroke="#ffffff05" 
            />
            <text 
              x={getX(i)} 
              y={height - 5} 
              fill="#ffffff30" 
              fontSize={10} 
              textAnchor="middle"
            >
              {d.day}
            </text>
            
            {/* Dots on line */}
            <circle cx={getX(i)} cy={getY(d.applied)} r={4} fill="#CCFF00" />
            <circle cx={getX(i)} cy={getY(d.responses)} r={4} fill="#00F0FF" />
          </g>
        ))}
      </svg>
    </div>
  );
}

function OverviewPanel({ status }: { status: DashboardStatus | null }) {
  const kpis = [
    { label: "Applied Today", value: "47", delta: "+12%", color: "#CCFF00" },
    { label: "This Week", value: "231", delta: "+8%", color: "#00F0FF" },
    { label: "Responses", value: "18", delta: "+22%", color: "#FF00FF" },
    { label: "Interviews", value: "4", delta: "+33%", color: "#CCFF00" },
    { label: "Jobs Scraped", value: String(status?.jobs_scraped ?? 0), delta: "live", color: "#00F0FF" },
    { label: "Applications", value: String(status?.applications_logged ?? 0), delta: "logged", color: "#E0E0E0" },
  ];

  return (
    <div className="space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {kpis.map((kpi) => (
          <div key={kpi.label}
            className="glass-panel rounded-2xl p-4 border border-white/5 hover:border-[#CCFF00]/20 transition-all duration-300">
            <p className="text-[10px] text-white/40 mb-1 uppercase tracking-widest">{kpi.label}</p>
            <p className="font-bold text-3xl" style={{ color: kpi.color }}>{kpi.value}</p>
            <p className="text-[10px] text-[#CCFF00] mt-1">{kpi.delta}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-panel rounded-2xl p-5 border border-white/5">
          <p className="text-[10px] text-white/40 mb-4 uppercase tracking-widest">Applications This Week</p>
          <CustomAreaChart />
        </div>

        {/* Quick batch apply */}
        <div className="glass-panel rounded-2xl p-5 border border-white/5 flex flex-col gap-4">
          <p className="text-[10px] text-white/40 uppercase tracking-widest">Quick Actions</p>
          <button
            onClick={async () => {
              await api("/api/jobs/scrape", {
                method: "POST",
                body: JSON.stringify({ keywords: ["software engineer"], location: "Remote", platforms: ["remotive", "remoteok", "hn"], max_jobs: 30 }),
              });
              alert("Scrape queued! Check Job Queue tab in ~15s");
            }}
            className="w-full py-3 rounded-xl font-bold text-black text-sm transition-all hover:scale-105"
            style={{ background: "#CCFF00" }}
          >
            ⚡ Quick Scrape
          </button>
          <button
            onClick={async () => {
              const consent = getCookie("applymind_creds_consent") === "true";
              if (!consent) {
                alert("Please configure your credentials and accept the Privacy Policy consent in the 'Job Queue' tab first.");
                return;
              }
              const creds = getCredentialsFromCookies();
              const r = await api<any>("/api/apply/batch", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ 
                  daily_limit: 20, 
                  min_score: 65,
                  credentials: creds
                }),
              });
              alert(r?.message ?? "No jobs to apply to yet. Scrape first!");
            }}
            className="w-full py-3 rounded-xl font-bold text-sm border border-[#00F0FF]/30 text-[#00F0FF] hover:bg-[#00F0FF]/10 transition-all"
          >
            ◈ Batch Apply (20)
          </button>
          <button
            onClick={async () => {
              const r = await api<any>("/api/analytics/weekly");
              if (r?.weekly_report) alert(r.weekly_report.slice(0, 500) + "…");
              else alert("Upload a resume and scrape jobs first!");
            }}
            className="w-full py-3 rounded-xl font-bold text-sm border border-[#FF00FF]/30 text-[#FF00FF] hover:bg-[#FF00FF]/10 transition-all"
          >
            ◉ Weekly Report
          </button>

          {/* Backend status */}
          <div className="mt-auto pt-4 border-t border-white/5">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status?.backend === "running" ? "bg-[#CCFF00] animate-pulse" : "bg-red-500"}`} />
              <span className="text-[10px] text-white/40">
                {status?.backend === "running" ? `Backend live · ${status.groq_model}` : "Backend offline"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// APPLICATIONS PANEL
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function ApplicationsPanel() {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await api<any>("/api/applications");
    if (data?.applications) {
      setApps(data.applications);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-5">
      <div className="flex justify-between items-center">
        <p className="text-[10px] text-white/40 uppercase tracking-widest">Application Submissions History</p>
        <button onClick={load} className="text-xs px-3 py-1.5 rounded-lg border border-white/10 hover:border-[#CCFF00]/40 transition-colors">
          🔄 Refresh
        </button>
      </div>

      {loading ? (
        <div className="glass-panel rounded-2xl p-10 text-center border border-white/5">
          <div className="w-3 h-3 rounded-full animate-ping mx-auto" style={{ background: "var(--acid)" }} />
        </div>
      ) : apps.length > 0 ? (
        <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-white/5 bg-white/1 text-white/40 font-bold uppercase tracking-wider">
                  <th className="p-4">Job Title</th>
                  <th className="p-4">Company</th>
                  <th className="p-4">Platform</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Date Applied</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app: any) => (
                  <tr key={app.id || app.job_id} className="border-b border-white/5 hover:bg-white/1 transition-all">
                    <td className="p-4 font-bold text-white">{app.job_title}</td>
                    <td className="p-4 text-white/70">{app.company}</td>
                    <td className="p-4 text-white/40 font-mono">{app.platform}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold"
                        style={{
                          background: (STATUS_COLORS[app.status] || "#888") + "20",
                          color: STATUS_COLORS[app.status] || "#888",
                          border: `1px solid ${(STATUS_COLORS[app.status] || "#888")}40`
                        }}>
                        {STATUS_LABELS[app.status] || app.status}
                      </span>
                    </td>
                    <td className="p-4 text-white/40">
                      {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString(undefined, {
                        year: 'numeric', month: 'short', day: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                      }) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl p-10 text-center border border-white/5">
          <p className="text-white/20 text-sm">No applications have been logged yet.</p>
          <p className="text-white/10 text-xs mt-2">Go to Job Queue → Scrape → then Overview → Batch Apply</p>
        </div>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ROOT DASHBOARD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export default function Dashboard() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);

  // Redirect if not logged in
  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  // Poll backend status every 5s
  useEffect(() => {
    if (!user) return;
    const check = async () => {
      const s = await api<DashboardStatus>("/status");
      if (s) { setStatus(s); setBackendOnline(true); }
      else setBackendOnline(false);
    };
    check();
    const iv = setInterval(check, 5000);
    return () => clearInterval(iv);
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-3 h-3 rounded-full animate-ping bg-[#CCFF00]" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect shortly
  }

  return (
    <div className="min-h-screen bg-black text-white flex" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>

      {/* Sidebar - Desktop */}
      <aside className={`hidden md:flex ${sidebarOpen ? "w-60" : "w-16"} shrink-0 border-r border-white/5 flex flex-col transition-all duration-300 bg-[#050505]`}>
        {/* Logo */}
        <div className="p-5 border-b border-white/5 flex items-center gap-3">
          <span className="text-[#CCFF00] font-bold text-xl shrink-0">⬡</span>
          {sidebarOpen && <span className="font-bold text-white text-base tracking-tight">ApplyMind</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all duration-200
                ${activeTab === item.id
                  ? "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20"
                  : "text-white/40 hover:text-white/70 hover:bg-white/3"
                }`}
            >
              <span className="text-base shrink-0">{item.icon}</span>
              {sidebarOpen && <span className="font-medium truncate">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Backend indicator */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full shrink-0 ${backendOnline ? "bg-[#CCFF00] animate-pulse" : "bg-red-500"}`} />
            {sidebarOpen && (
              <span className="text-[10px] text-white/30 truncate">
                {backendOnline ? "API Online" : "API Offline — run uvicorn"}
              </span>
            )}
          </div>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-4 text-white/20 hover:text-white/50 text-xs border-t border-white/5 transition-colors"
        >
          {sidebarOpen ? "← Collapse" : "→"}
        </button>
      </aside>

      {/* Sidebar Drawer - Mobile */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Overlay */}
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setMobileSidebarOpen(false)} />
          
          <aside className="relative w-60 h-full border-r border-white/5 flex flex-col bg-[#050505] p-5">
            <div className="flex justify-between items-center mb-6">
              <span className="text-[#CCFF00] font-bold text-xl">⬡</span>
              <span className="font-bold text-white text-base">ApplyMind</span>
              <button onClick={() => setMobileSidebarOpen(false)} className="text-white/40 hover:text-white text-sm">
                ✕
              </button>
            </div>
            <nav className="flex-1 space-y-1">
              {NAV_ITEMS.map(item => (
                <button
                  key={item.id}
                  onClick={() => { setActiveTab(item.id); setMobileSidebarOpen(false); }}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all duration-200
                    ${activeTab === item.id
                      ? "bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20"
                      : "text-white/40 hover:text-white/70 hover:bg-white/3"
                    }`}
                >
                  <span className="text-base shrink-0">{item.icon}</span>
                  <span className="font-medium truncate">{item.label}</span>
                </button>
              ))}
            </nav>
            <div className="pt-4 border-t border-white/5">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full shrink-0 ${backendOnline ? "bg-[#CCFF00] animate-pulse" : "bg-red-500"}`} />
                <span className="text-[10px] text-white/30 truncate">
                  {backendOnline ? "API Online" : "API Offline"}
                </span>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Main */}
      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="sticky top-0 z-20 bg-black/80 backdrop-blur-xl border-b border-white/5 px-8 py-4 flex items-center justify-between">
          <div className="flex items-center">
            {/* Hamburger Button */}
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="md:hidden p-2 -ml-2 mr-3 text-white/60 hover:text-white rounded-lg hover:bg-white/5"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 className="font-bold text-white text-lg capitalize">
                {NAV_ITEMS.find(n => n.id === activeTab)?.label ?? activeTab}
              </h1>
              <p className="text-white/30 text-xs mt-0.5">
                ApplyMind AI · {backendOnline ? `${status?.jobs_scraped ?? 0} jobs in queue` : "Backend offline"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {backendOnline && (
              <span className="text-[10px] px-3 py-1.5 rounded-full bg-[#CCFF00]/10 text-[#CCFF00] border border-[#CCFF00]/20 hidden sm:inline-block">
                Groq llama-3.3-70b ●
              </span>
            )}
            <a href="/" className="text-white/30 hover:text-white/70 text-xs transition-colors">← Home</a>
          </div>
        </header>

        {/* Content */}
        <div className="p-8">
          {activeTab === "overview" && <OverviewPanel status={status} />}
          {activeTab === "jobs" && <JobQueuePanel />}
          {activeTab === "resume" && <ResumePanel />}
          {activeTab === "market" && <MarketPanel />}
          {activeTab === "agents" && <AgentsPanel backendOnline={backendOnline} />}
          {activeTab === "applications" && <ApplicationsPanel />}
        </div>
      </main>

      <style jsx global>{`
        .glass-panel { background: rgba(255,255,255,0.02); }
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
      `}</style>
    </div>
  );
}
