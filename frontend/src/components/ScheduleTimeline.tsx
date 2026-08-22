import React, { useState } from 'react';
import type { Interview, Room, Company } from '../types';
import { Search, AlertCircle, LayoutGrid, ListFilter, X, FilterX } from 'lucide-react';

interface ScheduleTimelineProps {
  interviews: Interview[];
  rooms: Room[];
  companies?: Company[];
  selectedDay: number;
  onSelectDay: (day: number) => void;
  activeVersionId?: number;
}

export const ScheduleTimeline: React.FC<ScheduleTimelineProps> = ({
  interviews,
  rooms,
  selectedDay,
  onSelectDay,
  activeVersionId = 1,
}) => {
  const [viewMode, setViewMode] = useState<'gantt' | 'table'>('gantt');
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedInterview, setSelectedInterview] = useState<Interview | null>(null);

  const displayDay = selectedDay === 0 ? 1 : selectedDay;

  // Active Filter Count
  let activeFilterCount = 0;
  if (selectedDay !== 0) activeFilterCount++;
  if (statusFilter !== 'all') activeFilterCount++;
  if (search.trim() !== '') activeFilterCount++;

  const handleClearFilters = () => {
    onSelectDay(1);
    setStatusFilter('all');
    setSearch('');
  };

  const filteredInterviews = interviews.filter((iv) => {
    if (selectedDay !== 0 && iv.day !== selectedDay && iv.status !== 'unscheduled') {
      return false;
    }

    if (statusFilter !== 'all' && iv.status !== statusFilter) {
      return false;
    }

    if (search.trim() !== '') {
      const q = search.toLowerCase();
      const studMatch = iv.student_name?.toLowerCase().includes(q) || iv.student_id.toLowerCase().includes(q);
      const compMatch = iv.company_name?.toLowerCase().includes(q) || iv.company_id.toLowerCase().includes(q);
      const roomMatch = iv.room_name?.toLowerCase().includes(q) || iv.room_id?.toLowerCase().includes(q);
      if (!studMatch && !compMatch && !roomMatch) return false;
    }

    return true;
  });

  const scheduledList = filteredInterviews.filter((iv) => iv.status !== 'unscheduled');
  const unscheduledList = filteredInterviews.filter((iv) => iv.status === 'unscheduled');

  // Standard 24-Hour Time Format (09:00 - 17:00, no 12-hour wrap)
  const formatMinutes = (mins?: number) => {
    if (mins === undefined || mins === null) return '--:--';
    const totalMinutesFromMidnight = 540 + mins; // 09:00 AM start
    const h = Math.floor(totalMinutesFromMidnight / 60);
    const m = totalMinutesFromMidnight % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  };

  const calculateDurationMins = (start?: number, end?: number) => {
    if (start === undefined || end === undefined) return 30;
    return end - start;
  };

  // 24-Hour Time Slot Headers
  const timeSlotHeaders = Array.from({ length: 32 }, (_, i) => {
    const totalMins = 540 + i * 15;
    const h = Math.floor(totalMins / 60);
    const m = totalMins % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  });

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1.25rem' }}>
      {/* Header & Controls Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        {/* Day Selectors */}
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginRight: '0.2rem', textTransform: 'uppercase' }}>PLACEMENT DAY:</span>
          {[1, 2, 3, 4].map((d) => (
            <button
              key={d}
              className={`tab ${selectedDay === d ? 'active' : ''}`}
              onClick={() => onSelectDay(d)}
            >
              Day {d}
            </button>
          ))}
          <button
            className={`tab ${selectedDay === 0 ? 'active' : ''}`}
            onClick={() => onSelectDay(0)}
          >
            All Days (Overview)
          </button>
        </div>

        {/* View Switcher & Filter Tools */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Gantt Legend */}
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', fontSize: '0.68rem', fontWeight: 700, marginRight: '0.5rem', background: 'var(--bg-secondary)', padding: '0.25rem 0.6rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#38bdf8' }} />
              <span style={{ color: 'var(--text-secondary)' }}>SCHEDULED</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#10b981' }} />
              <span style={{ color: 'var(--text-secondary)' }}>NEWLY SCHEDULED</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#f59e0b' }} />
              <span style={{ color: 'var(--text-secondary)' }}>RESCHEDULED</span>
            </div>
          </div>

          <div style={{ display: 'flex', background: 'var(--bg-secondary)', padding: '0.2rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)' }}>
            <button
              className={`tab ${viewMode === 'gantt' ? 'active' : ''}`}
              onClick={() => setViewMode('gantt')}
              style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <LayoutGrid size={14} /> ROOM GANTT
            </button>
            <button
              className={`tab ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
              style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <ListFilter size={14} /> TABLE VIEW
            </button>
          </div>

          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '0.65rem', top: '0.55rem', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search student, company, room..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: '0.4rem 0.75rem 0.4rem 2.2rem',
                background: 'var(--bg-secondary)',
                color: '#fff',
                border: '1px solid var(--border-color)',
                borderRadius: '0.375rem',
                fontSize: '0.82rem',
                width: '240px',
              }}
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              background: 'var(--bg-secondary)',
              color: '#fff',
              border: '1px solid var(--border-color)',
              borderRadius: '0.375rem',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            <option value="all">All Statuses</option>
            <option value="scheduled">Scheduled</option>
            <option value="rescheduled">Rescheduled</option>
            <option value="cancelled">Cancelled</option>
            <option value="unscheduled">Unscheduled</option>
          </select>

          {activeFilterCount > 0 && (
            <button
              className="btn btn-outline"
              onClick={handleClearFilters}
              style={{ padding: '0.35rem 0.6rem', fontSize: '0.72rem', color: 'var(--accent-danger)', border: '1px solid rgba(239,68,68,0.3)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              title="Reset search and filters to baseline view"
            >
              <FilterX size={14} /> Clear Filters ({activeFilterCount})
            </button>
          )}
        </div>
      </div>

      {/* GANTT ROOM MATRIX VIEW */}
      {viewMode === 'gantt' ? (
        <div className="timeline-container" style={{ overflowX: 'auto', maxHeight: '560px', border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
          <div style={{ minWidth: '1350px' }}>
            {/* 24-Hour Time Axis Header */}
            <div style={{ display: 'grid', gridTemplateColumns: '160px repeat(32, 1fr)', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', position: 'sticky', top: 0, zIndex: 10 }}>
              <div style={{ padding: '0.6rem', fontSize: '0.72rem', fontWeight: 800, color: 'var(--accent-primary)', borderRight: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {selectedDay === 0 ? 'ROOMS (DAY 1 OVERVIEW)' : `ROOM MATRIX (DAY ${selectedDay})`}
              </div>
              {timeSlotHeaders.map((t, idx) => (
                <div key={idx} style={{ padding: '0.5rem 0.15rem', fontSize: '0.65rem', fontWeight: idx % 4 === 0 ? 800 : 500, color: idx % 4 === 0 ? '#f4f7fb' : '#475569', textAlign: 'center', borderRight: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)' }}>
                  {idx % 4 === 0 ? t : ''}
                </div>
              ))}
            </div>

            {/* Room Rows with Two-Line Hierarchy */}
            {rooms.map((r) => {
              const roomIvs = scheduledList.filter((iv) => iv.room_id === r.id && (iv.day === displayDay || selectedDay === 0));

              return (
                <div key={r.id} style={{ display: 'grid', gridTemplateColumns: '160px repeat(32, 1fr)', borderBottom: '1px solid var(--border-subtle)', minHeight: '46px', alignItems: 'center' }}>
                  {/* Clean Two-Line Room Label Column */}
                  <div style={{ padding: '0.45rem 0.75rem', borderRight: '1px solid var(--border-color)', background: 'rgba(13,20,34,0.6)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: '0.02em' }}>
                      {r.name.split(' (')[0].toUpperCase()}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 500, marginTop: '0.05rem' }}>
                      {r.building}
                    </div>
                  </div>

                  <div style={{ gridColumn: '2 / span 32', display: 'grid', gridTemplateColumns: 'repeat(32, 1fr)', height: '100%', position: 'relative', alignItems: 'center' }}>
                    {/* Background hourly and 15m gridlines */}
                    {Array.from({ length: 32 }).map((_, idx) => (
                      <div key={idx} style={{ height: '100%', borderRight: idx % 4 === 3 ? '1px solid rgba(255,255,255,0.08)' : '1px solid var(--border-subtle)' }} />
                    ))}

                    {/* Scheduled Interview Blocks */}
                    {roomIvs.map((iv) => {
                      if (iv.start_minutes === undefined || iv.end_minutes === undefined) return null;

                      const startSlot = Math.floor(iv.start_minutes / 15);
                      const neededSlots = Math.floor((iv.end_minutes - iv.start_minutes) / 15);

                      const isRescheduled = iv.status === 'rescheduled';
                      const isSelected = selectedInterview?.id === iv.id;
                      const bg = isSelected
                        ? 'linear-gradient(135deg, #f59e0b, #d97706)'
                        : isRescheduled
                        ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.85), rgba(217, 119, 6, 0.95))'
                        : iv.priority === 1
                        ? 'linear-gradient(135deg, rgba(56, 189, 248, 0.85), rgba(59, 130, 246, 0.95))'
                        : 'linear-gradient(135deg, rgba(99, 102, 241, 0.85), rgba(139, 92, 246, 0.95))';

                      const tooltipText = `Company: ${iv.company_name}\nStudent: ${iv.student_name} (${iv.student_id})\nTime: Day ${iv.day} | ${formatMinutes(iv.start_minutes)} - ${formatMinutes(iv.end_minutes)}\nPanel: ${iv.panel_id}\nRoom: ${iv.room_name || iv.room_id}\nStatus: ${iv.status.toUpperCase()}`;

                      return (
                        <div
                          key={iv.id}
                          onClick={() => setSelectedInterview(iv)}
                          style={{
                            position: 'absolute',
                            left: `${(startSlot / 32) * 100}%`,
                            width: `${(neededSlots / 32) * 100}%`,
                            height: '32px',
                            background: bg,
                            borderRadius: '0.35rem',
                            padding: '0.2rem 0.45rem',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            color: '#fff',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: isSelected ? '0 0 0 2px #38bdf8' : '0 2px 6px rgba(0,0,0,0.4)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            overflow: 'hidden',
                            whiteSpace: 'nowrap',
                            zIndex: isSelected ? 10 : 5,
                            transition: 'all 0.15s ease',
                          }}
                          title={tooltipText}
                        >
                          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {iv.company_name} • {iv.student_name?.split(' ')[0]}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* TABLE LIST VIEW */
        <div className="timeline-container" style={{ border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
          <table className="timeline-table">
            <thead>
              <tr>
                <th>Time Slot (24h)</th>
                <th>Day</th>
                <th>Student</th>
                <th>Company</th>
                <th>Room</th>
                <th>Panel</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {scheduledList.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No scheduled interviews match current search/filter criteria.
                  </td>
                </tr>
              ) : (
                scheduledList.map((iv) => (
                  <tr key={iv.id} onClick={() => setSelectedInterview(iv)} style={{ cursor: 'pointer' }}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-primary)' }}>
                      {formatMinutes(iv.start_minutes)} – {formatMinutes(iv.end_minutes)}
                    </td>
                    <td>
                      <span className="badge badge-info">Day {iv.day}</span>
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {iv.student_name} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({iv.student_id})</span>
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{iv.company_name}</td>
                    <td>{iv.room_name || iv.room_id || '--'}</td>
                    <td>{iv.panel_id ? `Panel ${iv.panel_id.split('-').pop()}` : '--'}</td>
                    <td>
                      <span className="badge badge-info">Tier {iv.priority}</span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          iv.status === 'rescheduled'
                            ? 'badge-warning'
                            : iv.status === 'scheduled'
                            ? 'badge-success'
                            : 'badge-danger'
                        }`}
                      >
                        {iv.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* UNSCHEDULED INTERVIEWS & CAPACITY LOG */}
      {unscheduledList.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--accent-warning)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <AlertCircle size={16} /> UNSCHEDULED INTERVIEWS & CAPACITY LOG ({unscheduledList.length.toLocaleString()})
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '0.75rem' }}>
            {unscheduledList.slice(0, 6).map((u) => (
              <div key={u.id} className="glass-card" style={{ background: 'rgba(245, 158, 11, 0.05)', padding: '0.85rem', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '0.82rem' }}>
                  <span>{u.student_name} ({u.student_id})</span>
                  <span style={{ color: 'var(--accent-warning)' }}>{u.company_name}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                  <strong>Refusal Reason:</strong> {u.refusal_reason || 'no_compatible_room'}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  <strong>Recommended Action:</strong> Coordinator room capacity override or tier re-prioritization.
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* INTERVIEW DETAIL RIGHT-SIDE INSPECTOR DRAWER */}
      {selectedInterview && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '520px', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
                Interview Inspector — Slot #{selectedInterview.id}
              </h3>
              <button className="btn btn-outline" style={{ padding: '0.2rem 0.4rem' }} onClick={() => setSelectedInterview(null)}>
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', marginTop: '1rem', fontSize: '0.82rem' }}>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Student Name</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{selectedInterview.student_name}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Student ID</span>
                <div style={{ fontWeight: 700, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>{selectedInterview.student_id}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Company</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{selectedInterview.company_name}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Placement Day</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Day {selectedInterview.day}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Start & End Time (24h)</span>
                <div style={{ fontWeight: 700, color: 'var(--accent-warning)', fontFamily: 'var(--font-mono)' }}>
                  {formatMinutes(selectedInterview.start_minutes)} – {formatMinutes(selectedInterview.end_minutes)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Duration</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {calculateDurationMins(selectedInterview.start_minutes, selectedInterview.end_minutes)} mins
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Room & Building</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedInterview.room_name || selectedInterview.room_id}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Panel ID</span>
                <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{selectedInterview.panel_id}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Priority Tier</span>
                <div>
                  <span className="badge badge-info">Tier {selectedInterview.priority}</span>
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Schedule Version</span>
                <div style={{ fontWeight: 700, color: 'var(--accent-purple)' }}>Version #{selectedInterview.version_id || activeVersionId}</div>
              </div>
            </div>

            <div style={{ marginTop: '0.85rem' }}>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Slot Status</span>
              <div style={{ marginTop: '0.2rem' }}>
                <span className={`badge ${selectedInterview.status === 'rescheduled' ? 'badge-warning' : 'badge-success'}`}>
                  {selectedInterview.status.toUpperCase()}
                </span>
              </div>
            </div>

            {selectedInterview.change_reason && (
              <div style={{ marginTop: '1rem', background: 'var(--bg-secondary)', padding: '0.65rem', borderRadius: '0.375rem', fontSize: '0.78rem', color: 'var(--text-secondary)', borderLeft: '3px solid var(--accent-primary)' }}>
                <strong>Disruption Audit Log:</strong> {selectedInterview.change_reason}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
