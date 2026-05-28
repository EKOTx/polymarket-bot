"use client";

import type { Metadata } from "next";
import { useState } from "react";
import { Send, CheckCircle } from "lucide-react";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, subject, message }),
      });
      if (!res.ok) throw new Error("Submission failed");
      setSubmitted(true);
    } catch {
      setError("Could not send message. Please email us directly at support@polymarketiq.com");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold text-[#e6edf3] mb-2">Contact</h1>
      <p className="text-sm text-[#6e7681] mb-8">
        Questions about the platform, security disclosures, data requests, or anything else.
      </p>

      {submitted ? (
        <div className="flex flex-col items-center gap-4 py-12 text-center">
          <CheckCircle className="w-12 h-12 text-emerald-400" />
          <h2 className="text-lg font-semibold text-[#e6edf3]">Message sent</h2>
          <p className="text-sm text-[#6e7681]">We aim to respond within 2 business days.</p>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[#6e7681] mb-1">Name</label>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:outline-none focus:border-[#388bfd]"
              />
            </div>
            <div>
              <label className="block text-xs text-[#6e7681] mb-1">Email</label>
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:outline-none focus:border-[#388bfd]"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-[#6e7681] mb-1">Subject</label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:outline-none focus:border-[#388bfd]"
            >
              <option value="">Select a topic…</option>
              <option value="general">General enquiry</option>
              <option value="billing">Billing / subscription</option>
              <option value="security">Security disclosure</option>
              <option value="data">Data / privacy request</option>
              <option value="bug">Bug report</option>
              <option value="feature">Feature request</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-[#6e7681] mb-1">Message</label>
            <textarea
              required
              rows={5}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3] focus:outline-none focus:border-[#388bfd] resize-none"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/30 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-[#388bfd] hover:bg-[#1f6feb] disabled:opacity-50 text-white px-6 py-2.5 rounded-md text-sm font-medium transition-colors"
          >
            {loading ? "Sending…" : "Send message"}
            {!loading && <Send className="w-4 h-4" />}
          </button>
        </form>
      )}
    </div>
  );
}
