import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import type {
  DashboardResponse,
  Interview,
  Room,
  Company,
  Panel,
  Student,
  DiffResponse,
  Notification,
} from './types';
import { Navbar } from './components/Navbar';
import { KpiBar } from './components/KpiBar';
import { ConflictCenter } from './components/ConflictCenter';
import { ScheduleTimeline } from './components/ScheduleTimeline';
import { DisruptionSimulator } from './components/DisruptionSimulator';
import { ReplanDiffModal } from './components/ReplanDiffModal';
import { StudentCompanyInspectors } from './components/StudentCompanyInspectors';

export const App: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [activeVersionId, setActiveVersionId] = useState<number>(1);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [panels, setPanels] = useState<Panel[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedDay, setSelectedDay] = useState<number>(1); // Day 1 selected by default

  const [diffModalOpen, setDiffModalOpen] = useState<boolean>(false);
  const [simulatorOpen, setSimulatorOpen] = useState<boolean>(false);
  const [currentDiff, setCurrentDiff] = useState<DiffResponse | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const loadDashboard = async (versionId?: number) => {
    try {
      setLoading(true);
      const dbRes = await api.getDashboard();

      const targetVerId = versionId || dbRes.active_version_id;
      setActiveVersionId(targetVerId);

      const [schedRes, roomsRes, compsRes, panelsRes, studRes, metricsRes, valRes] = await Promise.all([
        api.getSchedule(targetVerId),
        api.getRooms(),
        api.getCompanies(),
        api.getPanels(),
        api.getStudents(),
        api.getMetrics(targetVerId),
        api.validateSchedule(targetVerId),
      ]);

      setDashboard({
        ...dbRes,
        active_version_id: targetVerId,
        metrics: metricsRes,
        validation: valRes,
      });

      setInterviews(schedRes.interviews);
      setRooms(roomsRes);
      setCompanies(compsRes);
      setPanels(panelsRes);
      setStudents(studRes);

      const activeVerObj = dbRes.versions.find((v) => v.id === targetVerId);
      if (activeVerObj && activeVerObj.parent_id) {
        const diffRes = await api.getDiff(targetVerId, activeVerObj.parent_id);
        setCurrentDiff(diffRes);
        const notifRes = await api.getNotifications(targetVerId);
        setNotifications(notifRes);
      } else {
        setCurrentDiff(null);
        setNotifications([]);
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleSelectVersion = async (versionId: number) => {
    await loadDashboard(versionId);
  };

  const handleResetSeed = async () => {
    setLoading(true);
    await api.seedDataset(42);
    await api.generateSchedule();
    await loadDashboard(1);
    setLoading(false);
  };

  const handleApplyDisruption = async (payload: any) => {
    setLoading(true);
    const res = await api.replan(payload);
    setSimulatorOpen(false);
    await loadDashboard(res.version_id);
    setDiffModalOpen(true);
    setLoading(false);
  };

  const handleTriggerLiveDefense = async () => {
    setLoading(true);
    const res = await api.triggerLiveDefenseScenario();
    setSimulatorOpen(false);
    await loadDashboard(res.final_version_id);
    setDiffModalOpen(true);
    setLoading(false);
  };

  if (!dashboard) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: '#38bdf8' }}>
        <h2>Loading Placement Week Scheduler Dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Navbar
        activeVersionId={activeVersionId}
        versions={dashboard.versions}
        isValid={dashboard.validation.is_valid}
        onSelectVersion={handleSelectVersion}
        onResetSeed={handleResetSeed}
        onTriggerLiveDefense={handleTriggerLiveDefense}
        loading={loading}
      />

      <main className="main-content">
        <KpiBar metrics={dashboard.metrics} />

        <ConflictCenter
          validation={dashboard.validation}
          onOpenDiff={() => setDiffModalOpen(true)}
          onOpenSimulator={() => setSimulatorOpen(true)}
        />

        <ScheduleTimeline
          interviews={interviews}
          rooms={rooms}
          companies={companies}
          selectedDay={selectedDay}
          onSelectDay={setSelectedDay}
          activeVersionId={activeVersionId}
        />

        <StudentCompanyInspectors activeVersionId={activeVersionId} />
      </main>

      {simulatorOpen && (
        <DisruptionSimulator
          companies={companies}
          rooms={rooms}
          panels={panels}
          students={students}
          onClose={() => setSimulatorOpen(false)}
          onApplyDisruption={handleApplyDisruption}
          onTriggerLiveDefense={handleTriggerLiveDefense}
          loading={loading}
          activeVersionId={activeVersionId}
        />
      )}

      {diffModalOpen && (
        <ReplanDiffModal
          diff={currentDiff}
          notifications={notifications}
          onClose={() => setDiffModalOpen(false)}
        />
      )}
    </div>
  );
};

export default App;
