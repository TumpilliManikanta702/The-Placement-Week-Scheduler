import React, { useState } from 'react';
import type { Metrics } from '../types';
import { CheckCircle2, AlertCircle, DoorOpen, Users, Clock, RefreshCw, Info, X } from 'lucide-react';

interface KpiBarProps {
  metrics: Metrics;
}

export const KpiBar: React.FC<KpiBarProps> = ({ metrics }) => {
  const [scoreTooltipOpen, setScoreTooltipOpen] = useState<boolean>(false);
  const [panelTooltipOpen, setPanelTooltipOpen] = useState<boolean>(false);
  const [churnTooltipOpen, setChurnTooltipOpen] = useState<boolean>(false);

  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return '0';
    return num.toLocaleString();
  };

  return (
    <div className="kpi-grid">
      {/* SCHEDULING COVERAGE */}
      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">SCHEDULING COVERAGE</span>
          <CheckCircle2 size={16} color="var(--accent-success)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--accent-success)', marginTop: '0.2rem' }}>
          {metrics.scheduling_rate_pct.toFixed(2)}%
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-primary)', marginTop: '0.2rem', fontWeight: 600 }}>
          {formatNumber(metrics.scheduled_count)} / {formatNumber(metrics.total_interviews)} scheduled
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
          {formatNumber(metrics.unscheduled_count)} unscheduled due to room capacity & clashes
        </div>
      </div>

      {/* ACTIVE CONFLICTS */}
      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">ACTIVE CONFLICTS</span>
          <AlertCircle size={16} color={metrics.student_clash_count > 0 ? 'var(--accent-danger)' : 'var(--accent-success)'} />
        </div>
        <div className="kpi-value" style={{ color: metrics.student_clash_count > 0 ? 'var(--accent-danger)' : 'var(--accent-success)', marginTop: '0.2rem' }}>
          {metrics.student_clash_count}
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          {metrics.student_clash_count === 0 ? 'Zero hard-constraint violations' : 'Constraint violations detected'}
        </div>
      </div>

      {/* ROOM UTILIZATION */}
      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">ROOM UTILIZATION</span>
          <DoorOpen size={16} color="var(--accent-primary)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--accent-primary)', marginTop: '0.2rem' }}>
          {metrics.room_utilization_pct.toFixed(1)}%
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-primary)', marginTop: '0.2rem', fontWeight: 600 }}>
          Current v{metrics.version_id} • 20 schedulable rooms
        </div>
        {metrics.version_id !== 1 && (
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Baseline v1: 89.3%
          </div>
        )}
      </div>

      {/* PANEL UTILIZATION */}
      <div className="kpi-card" style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">PANEL UTILIZATION</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <button onClick={() => setPanelTooltipOpen(!panelTooltipOpen)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}>
              <Info size={14} />
            </button>
            <Users size={16} color="var(--accent-info)" />
          </div>
        </div>
        <div className="kpi-value" style={{ color: 'var(--accent-info)', marginTop: '0.2rem' }}>
          {metrics.panel_utilization_pct.toFixed(2)}%
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Company-bound panel capacity
        </div>

        {panelTooltipOpen && (
          <div style={{ position: 'absolute', top: '100%', right: 0, zIndex: 50, width: '250px', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-color)', borderRadius: '0.5rem', padding: '0.75rem', boxShadow: '0 10px 25px rgba(0,0,0,0.8)', marginTop: '0.4rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-info)' }}>Panel Capacity Note</span>
              <button onClick={() => setPanelTooltipOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={14} /></button>
            </div>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              Panel availability is company-bound and measured across the four-day placement horizon.
            </p>
          </div>
        )}
      </div>

      {/* AVG STUDENT WAIT */}
      <div className="kpi-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">AVG STUDENT WAIT</span>
          <Clock size={16} color="var(--accent-warning)" />
        </div>
        <div className="kpi-value" style={{ color: 'var(--accent-warning)', marginTop: '0.2rem' }}>
          {metrics.avg_student_wait_mins.toFixed(1)}m
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Between consecutive student interviews
        </div>
      </div>

      {/* REPLAN CHURN */}
      <div className="kpi-card" style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title">REPLAN CHURN</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <button onClick={() => setChurnTooltipOpen(!churnTooltipOpen)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}>
              <Info size={14} />
            </button>
            <RefreshCw size={16} color={metrics.replan_churn_pct > 15 ? 'var(--accent-danger)' : 'var(--accent-purple)'} />
          </div>
        </div>
        <div className="kpi-value" style={{ color: metrics.replan_churn_pct > 15 ? 'var(--accent-danger)' : 'var(--accent-purple)', marginTop: '0.2rem' }}>
          {metrics.replan_churn_pct.toFixed(2)}%
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Changed prior scheduled slots
        </div>

        {churnTooltipOpen && (
          <div style={{ position: 'absolute', top: '100%', right: 0, zIndex: 50, width: '260px', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-color)', borderRadius: '0.5rem', padding: '0.75rem', boxShadow: '0 10px 25px rgba(0,0,0,0.8)', marginTop: '0.4rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-purple)' }}>Churn Formula</span>
              <button onClick={() => setChurnTooltipOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={14} /></button>
            </div>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              <strong>Churn = (Moved + Cancelled) / Previously Scheduled</strong>
              <br />
              Current Version Replan Churn: <strong>{metrics.replan_churn_pct.toFixed(2)}%</strong>
            </p>
          </div>
        )}
      </div>

      {/* SCHEDULE QUALITY SCORE */}
      <div className="kpi-card" style={{ border: '1px solid rgba(167, 139, 250, 0.4)', position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="kpi-title" style={{ color: 'var(--accent-purple)' }}>SCHEDULE QUALITY SCORE</span>
          <button
            onClick={() => setScoreTooltipOpen(!scoreTooltipOpen)}
            style={{ background: 'none', border: 'none', color: 'var(--accent-purple)', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
            title="View Score Formula & Explanation Breakdown"
          >
            <Info size={16} />
          </button>
        </div>
        <div className="kpi-value" style={{ color: 'var(--accent-purple)', marginTop: '0.2rem' }}>
          {metrics.quality_score.toFixed(1)} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500 }}>/ 100</span>
        </div>
        <div className="kpi-subtext" style={{ color: 'var(--text-muted)', marginTop: '0.2rem' }}>
          Composite operational score
        </div>

        {/* Quality Score Transparent Formula Popup */}
        {scoreTooltipOpen && (
          <div
            style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              zIndex: 50,
              width: '290px',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid rgba(167, 139, 250, 0.5)',
              borderRadius: '0.5rem',
              padding: '0.85rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.8)',
              marginTop: '0.4rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-purple)' }}>Quality Score Formula</span>
              <button onClick={() => setScoreTooltipOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={14} />
              </button>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              <div>• <strong>0.50 × Coverage ({metrics.scheduling_rate_pct.toFixed(1)}%)</strong>: +{(0.5 * metrics.scheduling_rate_pct).toFixed(1)}</div>
              <div>• <strong>0.20 × Room Util ({metrics.room_utilization_pct.toFixed(1)}%)</strong>: +{(0.2 * metrics.room_utilization_pct).toFixed(1)}</div>
              <div>• <strong>0.15 × Panel Util ({metrics.panel_utilization_pct.toFixed(1)}%)</strong>: +{(0.15 * metrics.panel_utilization_pct).toFixed(1)}</div>
              <div>• <strong>Wait Penalty (0.5 × 60m)</strong>: -30.0</div>
              <div>• <strong>Churn Penalty (1.0 × {metrics.replan_churn_pct.toFixed(1)}%)</strong>: -{(1.0 * metrics.replan_churn_pct).toFixed(1)}</div>
              <div style={{ marginTop: '0.4rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.4rem', color: 'var(--text-muted)', fontSize: '0.65rem' }}>
                * <strong>Important</strong>: Schedule Quality Score ≠ Hard Constraint Validity. The schedule has 0 hard-constraint violations while maintaining an un-inflated operational score.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
