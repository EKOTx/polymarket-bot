"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Menu, X, BarChart2 } from "lucide-react";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#0d1117]/95 backdrop-blur-md border-b border-[#30363d]"
          : "bg-transparent"
      }`}
    >
      <nav className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded bg-[#388bfd] flex items-center justify-center">
            <BarChart2 className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-[#e6edf3] text-sm tracking-tight">
            Polymarket<span className="text-[#388bfd]">IQ</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-[#8b949e] hover:text-[#e6edf3] transition-colors"
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/privacy"
            className="text-sm text-[#8b949e] hover:text-[#e6edf3] transition-colors"
          >
            Legal
          </Link>
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-[#8b949e] hover:text-[#e6edf3] transition-colors px-3 py-1.5"
          >
            Sign In
          </Link>
          <Link
            href="#waitlist"
            className="text-sm bg-[#388bfd] hover:bg-[#1f6feb] text-white px-4 py-1.5 rounded-md font-medium transition-colors"
          >
            Join Waitlist
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-[#6e7681] hover:text-[#e6edf3]"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-[#0d1117] border-b border-[#30363d] px-4 py-4 space-y-3">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="block text-sm text-[#8b949e] hover:text-[#e6edf3] py-1"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </Link>
          ))}
          <div className="pt-2 flex flex-col gap-2">
            <Link href="/login" className="text-sm text-[#8b949e] py-1" onClick={() => setOpen(false)}>
              Sign In
            </Link>
            <Link
              href="#waitlist"
              className="text-sm bg-[#388bfd] text-white px-4 py-2 rounded-md font-medium text-center"
              onClick={() => setOpen(false)}
            >
              Join Waitlist
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
