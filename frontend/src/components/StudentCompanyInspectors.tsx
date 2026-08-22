import React, { useState, useEffect } from 'react';
import type { Student, Company } from '../types';
import { api } from '../services/api';
import { User, Building2, Search } from 'lucide-react';

interface InspectorProps {
  activeVersionId: number;
}

export const StudentCompanyInspectors: React.FC<InspectorProps> = ({ activeVersionId }) => {
  const [tab, setTab] = useState<'students' | 'companies'>('students');
  const [students, setStudents] = useState<Student[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [search, setSearch] = useState<string>('');
  const [selectedStudent, setSelectedStudent] = useState<any>(null);

  useEffect(() => {
    api.getCompanies().then(setCompanies).catch(console.error);
    api.getStudents().then(setStudents).catch(console.error);
  }, []);

  const handleSelectStudent = (id: string) => {
    api.getStudentDetails(id, activeVersionId).then(setSelectedStudent).catch(console.error);
  };

  const filteredStudents = students.filter(
    (s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.id.toLowerCase().includes(search.toLowerCase()) || s.branch.toLowerCase().includes(search.toLowerCase())
  );

  const filteredCompanies = companies.filter(
    (c) => c.name.toLowerCase().includes(search.toLowerCase()) || c.id.toLowerCase().includes(search.toLowerCase()) || c.company_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="tabs">
          <button className={`tab ${tab === 'students' ? 'active' : ''}`} onClick={() => setTab('students')}>
            <User size={16} /> Student Directory (800)
          </button>
          <button className={`tab ${tab === 'companies' ? 'active' : ''}`} onClick={() => setTab('companies')}>
            <Building2 size={16} /> Company Directory (35)
          </button>
        </div>

        <div style={{ position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.6rem', top: '0.6rem', color: '#94a3b8' }} />
          <input
            type="text"
            placeholder="Search directory..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem 0.45rem 2.2rem',
              background: '#1e293b',
              color: '#fff',
              border: '1px solid var(--border-color)',
              borderRadius: '0.375rem',
              fontSize: '0.85rem',
            }}
          />
        </div>
      </div>

      {tab === 'students' && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedStudent ? '1fr 1fr' : '1fr', gap: '1rem' }}>
          <div className="timeline-container" style={{ maxHeight: '350px', overflowY: 'auto' }}>
            <table className="timeline-table">
              <thead>
                <tr>
                  <th>Student ID</th>
                  <th>Name</th>
                  <th>Branch</th>
                  <th>CGPA</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.slice(0, 50).map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{s.id}</td>
                    <td style={{ fontWeight: 600 }}>{s.name}</td>
                    <td>{s.branch}</td>
                    <td style={{ fontWeight: 700, color: s.cgpa >= 8.5 ? '#10b981' : '#f8fafc' }}>{s.cgpa}</td>
                    <td>
                      {s.is_withdrawn ? (
                        <span className="badge badge-danger">WITHDRAWN</span>
                      ) : (
                        <span className="badge badge-success">ACTIVE</span>
                      )}
                    </td>
                    <td>
                      <button className="btn btn-outline" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }} onClick={() => handleSelectStudent(s.id)}>
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedStudent && (
            <div className="glass-card" style={{ background: 'rgba(15, 23, 42, 0.9)', padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>
                  {selectedStudent.student.name} ({selectedStudent.student.id})
                </h4>
                <button className="btn btn-outline" style={{ padding: '0.2rem 0.4rem' }} onClick={() => setSelectedStudent(null)}>
                  ✕
                </button>
              </div>

              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem', fontSize: '0.85rem', color: '#94a3b8' }}>
                <div>Branch: <strong style={{ color: '#fff' }}>{selectedStudent.student.branch}</strong></div>
                <div>CGPA: <strong style={{ color: '#10b981' }}>{selectedStudent.student.cgpa}</strong></div>
              </div>

              <h5 style={{ marginTop: '1rem', fontSize: '0.85rem', fontWeight: 700, color: '#06b6d4' }}>
                Shortlisted Companies ({selectedStudent.shortlisted_companies.length})
              </h5>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                {selectedStudent.shortlisted_companies.map((c: any) => (
                  <span key={c.id} style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 600 }}>
                    {c.name}
                  </span>
                ))}
              </div>

              <h5 style={{ marginTop: '1rem', fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
                Scheduled Interviews in Version #{activeVersionId}
              </h5>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.35rem' }}>
                {selectedStudent.interviews.length === 0 ? (
                  <p style={{ fontSize: '0.8rem', color: '#64748b' }}>No interviews scheduled.</p>
                ) : (
                  selectedStudent.interviews.map((iv: any) => (
                    <div key={iv.id} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem', borderRadius: '0.375rem', fontSize: '0.8rem' }}>
                      <strong>Day {iv.day}</strong> — {iv.company_name} in {iv.room_name || iv.room_id} ({iv.status})
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'companies' && (
        <div className="timeline-container" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <table className="timeline-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Company Name</th>
                <th>Category</th>
                <th>Priority</th>
                <th>CGPA Cutoff</th>
                <th>Eligible Branches</th>
                <th>Panels</th>
                <th>Duration</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredCompanies.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{c.id}</td>
                  <td style={{ fontWeight: 700, color: '#f8fafc' }}>{c.name}</td>
                  <td>{c.company_type}</td>
                  <td>
                    <span className="badge badge-info">Tier {c.priority_tier}</span>
                  </td>
                  <td style={{ fontWeight: 700, color: '#10b981' }}>{c.cgpa_cutoff}</td>
                  <td style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{c.eligible_branches.join(', ')}</td>
                  <td>{c.panel_count} panels</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{c.interview_duration} mins</td>
                  <td>
                    {c.arrival_status === 'delayed' ? (
                      <span className="badge badge-danger">DELAYED {c.delay_hours}h</span>
                    ) : (
                      <span className="badge badge-success">ON TIME</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
