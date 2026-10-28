"use client";

import { Menu } from "lucide-react";
import type { ReactNode } from "react";

/** The college bar across the top of every page: crest, institution and system name. */
export function TopBar({ right, onMenu }: { right?: ReactNode; onMenu?: () => void }) {
  return (
    <header className="no-print">
      <div className="bg-brand text-white">
        <div className="flex items-center gap-3 px-4 py-2.5 lg:px-6">
          {onMenu && (
            <button className="rounded p-1.5 text-white/90 hover:bg-white/10 lg:hidden" onClick={onMenu} aria-label="Open menu">
              <Menu size={20} />
            </button>
          )}
          {/* eslint-disable-next-line @next/next/no-img-element -- static export serves files as they are */}
          <img src="/crest.png" alt="Yaba College of Technology crest" className="h-10 w-10 shrink-0 rounded-full bg-white p-0.5" />
          {/* On a phone the crest stands for the college and the system name wraps instead of being cut off. */}
          <div className="min-w-0 leading-tight">
            <p className="hidden truncate text-[11px] font-medium uppercase tracking-wider text-white/75 sm:block">Yaba College of Technology</p>
            <p className="text-sm font-semibold sm:truncate sm:text-base">Student Performance Prediction System</p>
          </div>
          {right && <div className="ml-auto flex shrink-0 items-center gap-3">{right}</div>}
        </div>
      </div>
      <div className="h-[3px] bg-gold" />
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="no-print border-t border-line bg-surface px-4 py-3 text-xs text-muted lg:px-6">
      Department of Computer Science, School of Information and Communications Technology · Yaba College of Technology, Lagos
    </footer>
  );
}
