import React, { useState, useRef, useEffect } from 'react';
import { Calendar, RefreshCw, Zap, ShieldCheck, AlertTriangle, GitBranch, Info, ChevronDown, Check } from 'lucide-react';
import type { ScheduleVersion } from '../types';

interface NavbarProps {
  activeVersionId: number;
  versions: ScheduleVersion[];
  isValid: boolean;
  onSelectVersion: (versionId: number) => void;
  onResetSeed: () => void;
  onTriggerLiveDefense: () => void;
  loading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeVersionId,
  versions,
  isValid,
  onSelectVersion,
  onResetSeed,
  onTriggerLiveDefense,
  loading,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation for dropdown
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setDropdownOpen(false);
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const currentIndex = versions.findIndex((v) => v.id === activeVersionId);
      if (e.key === 'ArrowDown' && currentIndex < versions.length - 1) {
        onSelectVersion(versions[currentIndex + 1].id);
      } else if (e.key === 'ArrowUp' && currentIndex > 0) {
        onSelectVersion(versions[currentIndex - 1].id);
      }
    }
  };

  const getVersionBadge = (v: ScheduleVersion) => {
    if (v.id === 1) return { label: 'INITIAL', bg: 'rgba(56,189,248,0.12)', color: '#38bdf8' };
    if (v.id === 2) return { label: 'COMPANY DELAY', bg: 'rgba(245,158,11,0.12)', color: '#f59e0b' };
    if (v.id === 3) return { label: 'PANEL DROP', bg: 'rgba(239,68,68,0.12)', color: '#ef4444' };
    if (v.id === 4) return { label: 'STUDENT WITHDRAWAL', bg: 'rgba(167,139,250,0.12)', color: '#a78bfa' };
    return { label: (v.trigger_event || 'REPLAN').toUpperCase(), bg: 'rgba(148,163,184,0.12)', color: '#94a3b8' };
  };

  const getVersionTitle = (v: ScheduleVersion) => {
    if (v.id === 1) return 'v1 — Baseline Initial Schedule';
    if (v.id === 2) return 'v2 — TCS Digital Delay · 3h';
    if (v.id === 3) return 'v3 — Panel C01-P1 Drop';
    if (v.id === 4) return 'v4 — 15 Student Withdrawals';
    return `v${v.id} — ${v.summary || v.trigger_event}`;
  };

  const activeVerObj = versions.find((v) => v.id === activeVersionId) || versions[0];

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div className="brand-title">
          <div style={{ background: '#0284c7', padding: '0.4rem', borderRadius: '0.375rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Calendar size={18} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, letterSpacing: '0.02em', color: '#f4f7fb' }}>
              MIRAI LABS <span style={{ color: '#38bdf8', fontWeight: 600 }}>| Placement Operations</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#9aa8bc', fontWeight: 500 }}>
              Placement Week Scheduler & Disruption Replanner
            </div>
          </div>
        </div>

        {/* System Health Indicator Badge */}
        <div
          className={`badge ${isValid ? 'badge-success' : 'badge-danger'}`}
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.72rem', fontWeight: 700, borderRadius: '0.375rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          title="Independent validator confirms zero student, room, panel, or working-hour violations."
        >
          {isValid ? (
            <>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              <ShieldCheck size={14} />
              <span>VALID SCHEDULE · 0 HARD-CONSTRAINT VIOLATIONS</span>
            </>
          ) : (
            <>
              <AlertTriangle size={14} />
              <span>HARD CONFLICTS DETECTED</span>
            </>
          )}
        </div>
      </div>

      {/* Version Selector & Header Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Custom Accessible Version Dropdown Popover */}
        <div style={{ position: 'relative' }} ref={dropdownRef} onKeyDown={handleKeyDown}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => setDropdownOpen((prev) => !prev)}
            style={{
              padding: '0.4rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              borderColor: 'var(--border-color)',
              background: 'var(--bg-surface)',
              cursor: 'pointer',
            }}
            aria-haspopup="listbox"
            aria-expanded={dropdownOpen}
            aria-label="Select schedule version"
          >
            <GitBranch size={14} color="#38bdf8" />
            <span style={{ color: '#66758a', fontSize: '0.7rem', textTransform: 'uppercase' }}>VERSION:</span>
            <span style={{ color: '#f4f7fb' }}>{activeVerObj ? getVersionTitle(activeVerObj) : 'v1 Baseline'}</span>
            <ChevronDown size={14} color="#9aa8bc" style={{ transform: dropdownOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s ease' }} />
          </button>

          {dropdownOpen && (
            <div
              role="listbox"
              style={{
                position: 'absolute',
                top: '115%',
                right: 0,
                width: '320px',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                padding: '0.45rem',
                boxShadow: '0 12px 30px rgba(0,0,0,0.6)',
                zIndex: 2000,
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <div style={{ padding: '0.3rem 0.5rem', fontSize: '0.68rem', fontWeight: 800, color: '#66758a', letterSpacing: '0.05em', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>VERSION LINEAGE</span>
                <Info size={12} />
              </div>

              {versions.map((v, idx) => {
                const badge = getVersionBadge(v);
                const isSelected = v.id === activeVersionId;

                return (
                  <React.Fragment key={v.id}>
                    {idx > 0 && (
                      <div style={{ textAlign: 'center', color: '#66758a', fontSize: '0.68rem', lineHeight: '0.6' }}>
                        ↓
                      </div>
                    )}

                    <div
                      role="option"
                      aria-selected={isSelected}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectVersion(v.id);
                        setDropdownOpen(false);
                      }}
                      style={{
                        padding: '0.45rem 0.6rem',
                        borderRadius: '0.35rem',
                        background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                        border: isSelected ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '0.78rem', fontWeight: isSelected ? 800 : 600, color: isSelected ? '#38bdf8' : '#f4f7fb', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          {getVersionTitle(v)}
                          {isSelected && <Check size={14} color="#38bdf8" />}
                        </div>
                        <div style={{ marginTop: '0.15rem' }}>
                          <span style={{ background: badge.bg, color: badge.color, padding: '0.08rem 0.35rem', borderRadius: '0.2rem', fontSize: '0.62rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                            {badge.label}
                          </span>
                        </div>
                      </div>
                    </div>
                  </React.Fragment>
                );
              })}
            </div>
          )}
        </div>

        {/* Primary CTA: Live Defense Scenario */}
        <button
          className="btn btn-danger"
          onClick={onTriggerLiveDefense}
          disabled={loading}
          style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', fontWeight: 700, borderRadius: '0.375rem', cursor: loading ? 'not-allowed' : 'pointer' }}
          title="Run the deterministic four-stage disruption scenario."
        >
          <Zap size={14} /> <span>LIVE DEFENSE SCENARIO</span>
        </button>

        {/* Secondary CTA: Reset Demo */}
        <button
          className="btn btn-outline"
          onClick={onResetSeed}
          disabled={loading}
          style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem', fontWeight: 600, borderRadius: '0.375rem', cursor: loading ? 'not-allowed' : 'pointer' }}
          title="Restore the clean Version 1 baseline."
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> <span>RESET DEMO</span>
        </button>
      </div>
    </header>
  );
};
