import React from 'react';
import { AlertOctagon, CheckCircle2, ShieldAlert, ArrowRight } from 'lucide-react';
import type { ValidationReport } from '../types';

interface ConflictCenterProps {
  validation: ValidationReport;
  onOpenDiff: () => void;
  onOpenSimulator: () => void;
}

export const ConflictCenter: React.FC<ConflictCenterProps> = ({
  validation,
  onOpenDiff,
  onOpenSimulator,
}) => {
  const hasViolations = validation.violations_count > 0;

  return (
    <div
      className="glass-card"
      style={{
        background: hasViolations
          ? 'linear-gradient(135deg, rgba(244, 63, 94, 0.12), rgba(15, 23, 42, 0.6))'
          : 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(15, 23, 42, 0.6))',
        border: hasViolations ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(16, 185, 129, 0.4)',
        padding: '1rem 1.25rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div
            style={{
              background: hasViolations ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              padding: '0.5rem',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {hasViolations ? (
              <AlertOctagon size={24} color="#f43f5e" />
            ) : (
              <CheckCircle2 size={24} color="#10b981" />
            )}
          </div>

          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: hasViolations ? '#f43f5e' : '#10b981', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {hasViolations
                ? `CONFLICT CENTER — ${validation.violations_count} HARD CONSTRAINT VIOLATIONS!`
                : 'CONFLICT CENTER — FEASIBLE & VALID PLACEMENT SCHEDULE'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '0.2rem' }}>
              {hasViolations
                ? 'Hard constraint clashes detected. Immediate operational replanning required.'
                : 'Independent schedule validator confirms zero student, room, panel, or working-hour clashes across all scheduled interviews.'}
            </p>
          </div>
        </div>

        {/* Operational CTAs */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            className="btn btn-outline"
            onClick={onOpenSimulator}
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', fontWeight: 600, borderRadius: '0.375rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <ShieldAlert size={15} color="#06b6d4" /> <span>Inject Disruption</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={onOpenDiff}
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', fontWeight: 600, borderRadius: '0.375rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <span>View Changes & Diff</span> <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {hasViolations && (
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {validation.violations.slice(0, 3).map((v, i) => (
            <div
              key={i}
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                padding: '0.6rem 0.85rem',
                borderRadius: '0.375rem',
                fontSize: '0.8rem',
                color: '#f8fafc',
                borderLeft: '4px solid #f43f5e',
                boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
              }}
            >
              <strong style={{ color: '#f43f5e' }}>[{v.severity}] {v.type}:</strong> {v.description}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
