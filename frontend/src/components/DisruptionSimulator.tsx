import React, { useState, useEffect } from 'react';
import { ShieldAlert, Zap, X, Play, AlertTriangle } from 'lucide-react';
import type { Company, Room, Panel, Student } from '../types';

interface DisruptionSimulatorProps {
  companies: Company[];
  rooms: Room[];
  panels: Panel[];
  students: Student[];
  onClose: () => void;
  onApplyDisruption: (payload: any) => void;
  onTriggerLiveDefense: () => void;
  loading: boolean;
  activeVersionId?: number;
}

export const DisruptionSimulator: React.FC<DisruptionSimulatorProps> = ({
  companies,
  rooms,
  panels,
  students,
  onClose,
  onApplyDisruption,
  onTriggerLiveDefense,
  loading,
  activeVersionId = 1,
}) => {
  const [type, setType] = useState<string>('company_delay');
  const [companyId, setCompanyId] = useState<string>(companies[0]?.id || 'C01');
  const [delayHours, setDelayHours] = useState<number>(3);
  const [panelId, setPanelId] = useState<string>(panels[0]?.id || 'C01-P1');
  const [studentId, setStudentId] = useState<string>(students[0]?.id || 'S001');
  const [roomId, setRoomId] = useState<string>(rooms[0]?.id || 'R01');
  const [effectiveDay, setEffectiveDay] = useState<number>(1);
  const [startMins, setStartMins] = useState<number>(0);
  const [endMins, setEndMins] = useState<number>(240);
  const [reason, setReason] = useState<string>('Maintenance / Water leakage');

  // Keep panelId synchronized when companyId or type changes
  const handleCompanyChange = (cId: string) => {
    setCompanyId(cId);
    const companyPanels = panels.filter((p) => p.company_id === cId);
    if (companyPanels.length > 0) {
      setPanelId(companyPanels[0].id);
    }
  };

  useEffect(() => {
    if (type === 'panel_drop') {
      const companyPanels = panels.filter((p) => p.company_id === companyId);
      if (companyPanels.length > 0 && !companyPanels.some((p) => p.id === panelId)) {
        setPanelId(companyPanels[0].id);
      }
    }
  }, [type, companyId, panels, panelId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = {
      disruption_type: type,
      effective_day: effectiveDay,
    };

    if (type === 'company_delay') {
      payload.company_id = companyId;
      payload.delay_hours = delayHours;
    } else if (type === 'panel_drop') {
      payload.company_id = companyId;
      payload.panel_id = panelId;
      payload.effective_time_mins = 0;
    } else if (type === 'student_withdrawal') {
      payload.student_id = studentId;
      payload.student_ids = [studentId];
      payload.effective_time_mins = 0;
    } else if (type === 'room_unavailable') {
      payload.room_id = roomId;
      payload.start_mins = startMins;
      payload.end_mins = endMins;
      payload.reason = reason;
    }

    onApplyDisruption(payload);
  };

  const filteredPanels = panels.filter((p) => p.company_id === companyId);

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '650px', padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShieldAlert size={26} color="#06b6d4" />
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Disruption Simulator Control Panel</h2>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                Simulate real-world operational disruptions and trigger minimal-disruption replanning.
              </p>
            </div>
          </div>
          <button className="btn btn-outline" onClick={onClose} style={{ padding: '0.3rem 0.5rem' }}>
            <X size={18} />
          </button>
        </div>

        {/* PROMINENT LIVE DEFENSE PRESET CONTROL BOX */}
        <div
          style={{
            marginTop: '1.25rem',
            background: 'linear-gradient(135deg, rgba(244,63,94,0.18), rgba(139,92,246,0.18))',
            border: '1px solid rgba(244,63,94,0.4)',
            borderRadius: '0.6rem',
            padding: '1.25rem',
            boxShadow: '0 4px 15px rgba(244,63,94,0.15)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h4 style={{ color: '#f43f5e', fontWeight: 800, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Zap size={18} /> MIRAI LABS LIVE DEFENSE SCENARIO
              </h4>
              <div style={{ fontSize: '0.8rem', color: '#e2e8f0', marginTop: '0.5rem', lineHeight: '1.5' }}>
                <div>• <strong>Recruiter:</strong> TCS Digital (Day-1 Mass Recruiter)</div>
                <div>• <strong>Disruption:</strong> 3-hour arrival delay</div>
                <div>• <strong>Panel:</strong> C01-P1 dropped out</div>
                <div>• <strong>Withdrawals:</strong> 15 students simultaneously</div>
              </div>

              {activeVersionId !== 1 && (
                <div style={{ marginTop: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: '#f59e0b', background: 'rgba(245,158,11,0.1)', padding: '0.35rem 0.6rem', borderRadius: '0.375rem', border: '1px solid rgba(245,158,11,0.3)' }}>
                  <AlertTriangle size={14} /> Run RESET DEMO first to execute the clean four-stage defense scenario (v1 ➔ v4).
                </div>
              )}
            </div>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-danger"
              onClick={onTriggerLiveDefense}
              disabled={loading}
              style={{ padding: '0.55rem 1.1rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '0.4rem', boxShadow: '0 2px 10px rgba(244,63,94,0.4)', cursor: loading ? 'not-allowed' : 'pointer' }}
            >
              <Play size={15} /> <span>EXECUTE LIVE DEFENSE SCENARIO</span>
            </button>
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border-color)', margin: '1.25rem 0' }} />

        {/* CUSTOM DISRUPTION FORM */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8' }}>Custom Single Disruption Execution</h4>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Disruption Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem',
                background: '#1e293b',
                color: '#fff',
                border: '1px solid var(--border-color)',
                borderRadius: '0.375rem',
                marginTop: '0.25rem',
                fontWeight: 600,
              }}
            >
              <option value="company_delay">Company Delay (Arrival Delay)</option>
              <option value="panel_drop">Panel Drop (Member Dropout)</option>
              <option value="student_withdrawal">Student Withdrawal</option>
              <option value="room_unavailable">Room Unavailability</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Effective Placement Day</label>
              <select
                value={effectiveDay}
                onChange={(e) => setEffectiveDay(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.6rem',
                  background: '#1e293b',
                  color: '#fff',
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.375rem',
                  marginTop: '0.25rem',
                }}
              >
                <option value={1}>Day 1</option>
                <option value={2}>Day 2</option>
                <option value={3}>Day 3</option>
                <option value={4}>Day 4</option>
              </select>
            </div>

            {type === 'company_delay' && (
              <>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Select Company</label>
                  <select
                    value={companyId}
                    onChange={(e) => handleCompanyChange(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.id}) — Day {c.placement_day}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Delay Duration (Hours)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    max="6"
                    value={delayHours}
                    onChange={(e) => setDelayHours(Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  />
                </div>
              </>
            )}

            {type === 'panel_drop' && (
              <>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Select Company</label>
                  <select
                    value={companyId}
                    onChange={(e) => handleCompanyChange(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} ({c.id})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Select Panel to Drop</label>
                  <select
                    value={panelId}
                    onChange={(e) => setPanelId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    {filteredPanels.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.id} (Panel #{p.panel_number})
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {type === 'student_withdrawal' && (
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Select Student</label>
                <select
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.375rem',
                    marginTop: '0.25rem',
                  }}
                >
                  {students.slice(0, 100).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.id}) — {s.branch} ({s.cgpa} CGPA)
                    </option>
                  ))}
                </select>
              </div>
            )}

            {type === 'room_unavailable' && (
              <>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Select Room</label>
                  <select
                    value={roomId}
                    onChange={(e) => setRoomId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    {rooms.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name} ({r.building})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Unavailable Window (Mins)</label>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input
                      type="number"
                      value={startMins}
                      onChange={(e) => setStartMins(Number(e.target.value))}
                      placeholder="Start (e.g. 0)"
                      style={{ width: '50%', padding: '0.5rem', background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '0.375rem' }}
                    />
                    <input
                      type="number"
                      value={endMins}
                      onChange={(e) => setEndMins(Number(e.target.value))}
                      placeholder="End (e.g. 240)"
                      style={{ width: '50%', padding: '0.5rem', background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '0.375rem' }}
                    />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8' }}>Reason</label>
                  <input
                    type="text"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.6rem',
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.375rem',
                      marginTop: '0.25rem',
                    }}
                  />
                </div>
              </>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-outline" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ cursor: loading ? 'not-allowed' : 'pointer' }}>
              <Play size={14} /> <span>Execute Minimal Disruption Replanner</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
