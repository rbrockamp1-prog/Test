"use client";

import { useEffect, useState } from "react";

interface Lead {
  company: string;
  role: string;
  bucket: string;
  resume: string;
  status: string;
  url: string;
  dateAdded: string;
  dateApplied: string;
  followUpDue: string;
  whyItFits: string;
  fitScore: string;
}

const STATUS_COLORS: Record<string, string> = {
  "To Apply": "bg-yellow-100 text-yellow-800",
  Applied: "bg-blue-100 text-blue-800",
  Interviewing: "bg-purple-100 text-purple-800",
  Offer: "bg-green-100 text-green-800",
  Rejected: "bg-red-100 text-red-800",
  "Follow-up Sent": "bg-indigo-100 text-indigo-800",
  Closed: "bg-gray-100 text-gray-600",
};

const BUCKET_COLORS: Record<string, string> = {
  A: "bg-rose-100 text-rose-700",
  C: "bg-amber-100 text-amber-700",
  D: "bg-emerald-100 text-emerald-700",
  E: "bg-sky-100 text-sky-700",
  F: "bg-violet-100 text-violet-700",
};

const STATUSES = ["To Apply", "Applied", "Interviewing", "Offer", "Rejected", "Follow-up Sent", "Closed"];

export default function Tracker() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("All");
  const [bucketFilter, setBucketFilter] = useState("All");
  const [updating, setUpdating] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function fetchLeads() {
    setLoading(true);
    try {
      const res = await fetch("/api/leads", { cache: "no-store" });
      if (!res.ok) throw new Error(await res.text());
      setLeads(await res.json());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchLeads(); }, []);

  async function setStatus(lead: Lead, status: string) {
    const key = `${lead.company}-${lead.role}`;
    setUpdating(key);
    const dateApplied = status === "Applied" ? new Date().toISOString().slice(0, 10) : undefined;
    await fetch("/api/leads/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company: lead.company, role: lead.role, status, dateApplied }),
    });
    await fetchLeads();
    setUpdating(null);
  }

  const buckets = ["All", ...Array.from(new Set(leads.map((l) => l.bucket))).sort()];
  const statuses = ["All", ...STATUSES];

  const visible = leads.filter((l) => {
    if (filter !== "All" && l.status !== filter) return false;
    if (bucketFilter !== "All" && l.bucket !== bucketFilter) return false;
    return true;
  });

  const stats = {
    total: leads.length,
    toApply: leads.filter((l) => l.status === "To Apply").length,
    applied: leads.filter((l) => l.status === "Applied").length,
    interviewing: leads.filter((l) => l.status === "Interviewing").length,
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-gray-500">
      Loading tracker…
    </div>
  );

  if (error) return (
    <div className="p-6 text-red-600 bg-red-50 rounded-lg">
      Error: {error}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total Leads", value: stats.total, color: "text-gray-900" },
          { label: "To Apply", value: stats.toApply, color: "text-yellow-700" },
          { label: "Applied", value: stats.applied, color: "text-blue-700" },
          { label: "Interviewing", value: stats.interviewing, color: "text-purple-700" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-sm text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Status:</span>
          <div className="flex gap-1 flex-wrap">
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  filter === s
                    ? "bg-gray-900 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Bucket:</span>
          <div className="flex gap-1">
            {buckets.map((b) => (
              <button
                key={b}
                onClick={() => setBucketFilter(b)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  bucketFilter === b
                    ? "bg-gray-900 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {b}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={fetchLeads}
          className="ml-auto px-4 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {visible.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No leads match this filter.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Company</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Role</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Bucket</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Fit</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Added</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {visible.map((lead) => {
                const key = `${lead.company}-${lead.role}`;
                const isExpanded = expanded === key;
                const isUpdating = updating === key;
                return (
                  <>
                    <tr
                      key={key}
                      className={`hover:bg-gray-50 transition-colors cursor-pointer ${isUpdating ? "opacity-50" : ""}`}
                      onClick={() => setExpanded(isExpanded ? null : key)}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{lead.company}</td>
                      <td className="px-4 py-3 text-gray-700 max-w-xs">
                        {lead.url ? (
                          <a
                            href={lead.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {lead.role}
                          </a>
                        ) : (
                          lead.role
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${BUCKET_COLORS[lead.bucket] ?? "bg-gray-100 text-gray-600"}`}>
                          {lead.bucket}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <div
                            className="h-1.5 rounded-full bg-emerald-500"
                            style={{ width: `${(parseInt(lead.fitScore) || 0) * 10}px` }}
                          />
                          <span className="text-xs text-gray-500">{lead.fitScore}/10</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={lead.status}
                          onChange={(e) => { e.stopPropagation(); setStatus(lead, e.target.value); }}
                          onClick={(e) => e.stopPropagation()}
                          disabled={isUpdating}
                          className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-gray-300 ${STATUS_COLORS[lead.status] ?? "bg-gray-100 text-gray-600"}`}
                        >
                          {STATUSES.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{lead.dateAdded}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{isExpanded ? "▲" : "▼"}</td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${key}-detail`} className="bg-gray-50">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                            <div>
                              <div className="font-medium text-gray-700 mb-1">Why it fits</div>
                              <div className="text-gray-600 leading-relaxed">{lead.whyItFits || "—"}</div>
                            </div>
                            <div className="space-y-2">
                              <div><span className="font-medium text-gray-700">Resume version: </span><span className="text-gray-600">{lead.resume}</span></div>
                              {lead.dateApplied && <div><span className="font-medium text-gray-700">Applied: </span><span className="text-gray-600">{lead.dateApplied}</span></div>}
                              {lead.followUpDue && <div><span className="font-medium text-gray-700">Follow-up due: </span><span className="text-gray-600">{lead.followUpDue}</span></div>}
                              {lead.url && (
                                <a
                                  href={lead.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-block mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
                                >
                                  View Job Posting →
                                </a>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
      <div className="text-xs text-gray-400 text-right">
        Showing {visible.length} of {leads.length} leads · Updates sync to Google Sheet
      </div>
    </div>
  );
}
