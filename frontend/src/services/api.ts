import type {
  DashboardResponse,
  Interview,
  ValidationReport,
  DiffResponse,
  Metrics,
  Student,
  Company,
  Room,
  Panel,
  Notification
} from '../types';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api`;

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error (${res.status}): ${errorText}`);
  }

  return res.json();
}

export const api = {
  getDashboard: () => fetchJson<DashboardResponse>(`${API_BASE_URL}/dashboard`),

  seedDataset: (seed: number = 42) =>
    fetchJson<{ status: string; version_id: number }>(`${API_BASE_URL}/seed?seed=${seed}`, {
      method: 'POST',
    }),

  generateSchedule: () =>
    fetchJson<{ version_id: number; scheduled_count: number; unscheduled_count: number }>(
      `${API_BASE_URL}/schedule/generate`,
      { method: 'POST' }
    ),

  getSchedule: (versionId: number, params?: { day?: number; company_id?: string; room_id?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.day) query.append('day', params.day.toString());
    if (params?.company_id) query.append('company_id', params.company_id);
    if (params?.room_id) query.append('room_id', params.room_id);
    if (params?.status) query.append('status', params.status);

    return fetchJson<{ version_id: number; count: number; interviews: Interview[] }>(
      `${API_BASE_URL}/schedule/${versionId}?${query.toString()}`
    );
  },

  validateSchedule: (versionId: number) =>
    fetchJson<ValidationReport>(`${API_BASE_URL}/schedule/validate/${versionId}`, {
      method: 'POST',
    }),

  replan: (payload: any) =>
    fetchJson<any>(`${API_BASE_URL}/replan`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  triggerLiveDefenseScenario: () =>
    fetchJson<any>(`${API_BASE_URL}/replan/live-defense`, {
      method: 'POST',
    }),

  getDiff: (newVersionId: number, oldVersionId: number) =>
    fetchJson<DiffResponse>(`${API_BASE_URL}/diff/${newVersionId}/${oldVersionId}`),

  getMetrics: (versionId: number) =>
    fetchJson<Metrics>(`${API_BASE_URL}/metrics/${versionId}`),

  getStudents: (search?: string, branch?: string) => {
    const query = new URLSearchParams();
    if (search) query.append('search', search);
    if (branch) query.append('branch', branch);
    return fetchJson<Student[]>(`${API_BASE_URL}/students?${query.toString()}`);
  },

  getStudentDetails: (studentId: string, versionId?: number) => {
    const query = versionId ? `?version_id=${versionId}` : '';
    return fetchJson<any>(`${API_BASE_URL}/students/${studentId}${query}`);
  },

  getCompanies: () => fetchJson<Company[]>(`${API_BASE_URL}/companies`),

  getRooms: () => fetchJson<Room[]>(`${API_BASE_URL}/rooms`),

  getPanels: () => fetchJson<Panel[]>(`${API_BASE_URL}/panels`),

  getNotifications: (versionId: number) =>
    fetchJson<Notification[]>(`${API_BASE_URL}/notifications/${versionId}`),
};
