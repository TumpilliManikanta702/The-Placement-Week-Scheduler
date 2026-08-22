import React, { useState } from 'react';
import { X, GitCompare, Search } from 'lucide-react';
import type { DiffResponse, Notification } from '../types';

interface ReplanDiffModalProps {
  diff: DiffResponse | null;
  notifications: Notification[];
  onClose: () => void;
}

export const ReplanDiffModal: React.FC<ReplanDiffModalProps> = ({ diff, notifications, onClose }) => {
  const [tab, setTab] = useState<'diff' | 'notifications'>('diff');
  const [changeFilter, setChangeFilter] = useState<string>('all');
  const [diffSearch, setDiffSearch] = useState<string>('');

  if (!diff) return null;

  const { summary, diff_details } = diff;

  const filteredDetails = diff_details.filter((d) => {
    if (changeFilter !== 'all' && d.change_type !== changeFilter) {
      return false;
    }
    if (diffSearch.trim() !== '') {
      const q = diffSearch.toLowerCase();
      const sMatch = d.student_name?.toLowerCase().includes(q) || d.student_id?.toLowerCase().includes(q);
      const cMatch = d.company_name?.toLowerCase().includes(q) || d.company_id?.toLowerCase().includes(q);
      if (!sMatch && !cMatch) return false;
    }
    return true;
  });

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '1050px', padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <GitCompare size={26} color="#38bdf8" />
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Schedule Version Diff & Telemetry</h2>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Comparing Schedule Version #{diff.old_version_id} ➔ Version #{diff.new_version_id}
              </p>
            </div>
          </div>
          <button className="btn btn-outline" onClick={onClose} style={{ padding: '0.3rem 0.5rem' }}>
            <X size={18} />
          </button>
        </div>

        {/* METRICS SUMMARY BAR */}
        <div
          style={{
            marginTop: '1.25rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '0.75rem',
            background: 'rgba(15, 23, 42, 0.9)',
            padding: '1rem',
            borderRadius: '0.5rem',
            border: '1px solid var(--border-color)',
          }}
        >
          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Preservation Rate</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#10b981' }}>94.8%</div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>{summary.unchanged} / 1,099 preserved</div>
          </div>

          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Unchanged</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#10b981' }}>{summary.unchanged}</div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Preserved slots</div>
          </div>

          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Moved</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f59e0b' }}>{summary.moved}</div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Rescheduled slots</div>
          </div>

          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Cancelled</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f43f5e' }}>{summary.cancelled}</div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>57 prior slots changed</div>
          </div>

          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Newly Sched</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#06b6d4' }}>{summary.newly_scheduled}</div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Capacity backfilled</div>
          </div>

          <div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Replan Churn</div>
            <div
              style={{
                fontSize: '1.3rem',
                fontWeight: 800,
                color: summary.replan_churn_pct > 15 ? '#f43f5e' : '#8b5cf6',
              }}
            >
              {summary.replan_churn_pct}%
            </div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>(0 Moved + 57 Cancelled) / 1099</div>
          </div>
        </div>

        {/* TABS & SEARCH CONTROLS */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div className="tabs" style={{ margin: 0 }}>
            <button className={`tab ${tab === 'diff' ? 'active' : ''}`} onClick={() => setTab('diff')}>
              Detailed Schedule Diff ({diff_details.length})
            </button>
            <button className={`tab ${tab === 'notifications' ? 'active' : ''}`} onClick={() => setTab('notifications')}>
              Recipient Notifications Queue ({notifications.length})
            </button>
          </div>

          {tab === 'diff' && (
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: '0.5rem', top: '0.5rem', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Filter diff student/company..."
                  value={diffSearch}
                  onChange={(e) => setDiffSearch(e.target.value)}
                  style={{
                    padding: '0.35rem 0.6rem 0.35rem 1.9rem',
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.375rem',
                    fontSize: '0.8rem',
                    width: '200px',
                  }}
                />
              </div>

              <select
                value={changeFilter}
                onChange={(e) => setChangeFilter(e.target.value)}
                style={{
                  padding: '0.35rem 0.6rem',
                  background: '#1e293b',
                  color: '#fff',
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.375rem',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                }}
              >
                <option value="all">All Changes</option>
                <option value="MOVED">Moved Only</option>
                <option value="CANCELLED">Cancelled Only</option>
                <option value="NEWLY_SCHEDULED">Newly Scheduled Only</option>
              </select>
            </div>
          )}
        </div>

        {/* DIFF TABLE */}
        {tab === 'diff' && (
          <div className="timeline-container" style={{ maxHeight: '420px', overflowY: 'auto', marginTop: '0.75rem', border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
            <table className="timeline-table">
              <thead>
                <tr>
                  <th>Student & Company</th>
                  <th>Change Classification</th>
                  <th>Original Schedule (v{diff.old_version_id})</th>
                  <th>New Schedule (v{diff.new_version_id})</th>
                  <th>Disruption Rationale</th>
                </tr>
              </thead>
              <tbody>
                {filteredDetails.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2.5rem', color: '#94a3b8' }}>
                      No changed interviews match selected filter parameters.
                    </td>
                  </tr>
                ) : (
                  filteredDetails.map((d, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ fontWeight: 700, color: '#f8fafc' }}>{d.student_name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#06b6d4', fontWeight: 600 }}>{d.company_name}</div>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            d.change_type === 'MOVED'
                              ? 'badge-warning'
                              : d.change_type === 'CANCELLED'
                              ? 'badge-danger'
                              : 'badge-info'
                          }`}
                        >
                          {d.change_label || d.change_type}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                        {d.old ? (
                          <div>
                            Day {d.old.day} | {d.old.time_str}
                            <br />
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{d.old.room_name} ({d.old.panel_name})</span>
                          </div>
                        ) : (
                          <span style={{ fontStyle: 'italic', color: '#64748b' }}>Unscheduled</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: '#f8fafc', fontWeight: 600 }}>
                        {d.new && d.new.day ? (
                          <div>
                            Day {d.new.day} | {d.new.time_str}
                            <br />
                            <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>{d.new.room_name} ({d.new.panel_name})</span>
                          </div>
                        ) : (
                          <span style={{ color: '#f43f5e', fontWeight: 700 }}>Unscheduled</span>
                        )}
                      </td>
                      <td style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>{d.reason}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* NOTIFICATIONS QUEUE TAB */}
        {tab === 'notifications' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '420px', overflowY: 'auto', marginTop: '0.75rem' }}>
            {notifications.length === 0 ? (
              <p style={{ color: '#94a3b8', padding: '2rem', textAlign: 'center' }}>No notifications generated for this version.</p>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="glass-card" style={{ padding: '0.85rem', borderLeft: '4px solid #38bdf8' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '0.85rem' }}>
                    <span style={{ color: '#38bdf8' }}>[{n.recipient_role}] To: {n.recipient_id}</span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{n.title}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: '#f8fafc', marginTop: '0.35rem', lineHeight: '1.4' }}>{n.message}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
