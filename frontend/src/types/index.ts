export interface Company {
  id: string;
  name: string;
  priority_tier: number;
  cgpa_cutoff: number;
  eligible_branches: string[];
  panel_count: number;
  interview_duration: number;
  placement_day: number;
  expected_shortlist_size: number;
  company_type: string;
  arrival_status: string;
  delay_hours: number;
}

export interface Student {
  id: string;
  name: string;
  branch: string;
  cgpa: number;
  graduation_year: number;
  placement_status: string;
  is_withdrawn: boolean;
}

export interface Room {
  id: string;
  name: string;
  building: string;
  floor: number;
  capacity: number;
  status: string;
  unavailable_intervals: { day: number; start_mins: number; end_mins: number; reason?: string }[];
}

export interface Panel {
  id: string;
  company_id: string;
  company_name: string;
  panel_number: number;
  status: string;
}

export interface Interview {
  id: string;
  version_id: number;
  student_id: string;
  student_name?: string;
  company_id: string;
  company_name?: string;
  panel_id?: string;
  room_id?: string;
  room_name?: string;
  day?: number;
  start_minutes?: number;
  end_minutes?: number;
  status: 'scheduled' | 'completed' | 'cancelled' | 'withdrawn' | 'rescheduled' | 'unscheduled';
  priority: number;
  change_reason?: string;
  refusal_reason?: string;
}

export interface ScheduleVersion {
  id: number;
  parent_id?: number;
  trigger_event: string;
  summary: string;
  quality_score: number;
  created_at?: string;
}

export interface Metrics {
  version_id: number;
  total_interviews: number;
  scheduled_count: number;
  unscheduled_count: number;
  cancelled_count: number;
  scheduling_rate_pct: number;
  student_clash_count: number;
  room_utilization_pct: number;
  panel_utilization_pct: number;
  avg_student_wait_mins: number;
  replan_churn_pct: number;
  quality_score: number;
  validation_passed: boolean;
}

export interface ValidationReport {
  is_valid: boolean;
  violations_count: number;
  summary: {
    student_conflicts: number;
    room_conflicts: number;
    panel_conflicts: number;
    working_hour_violations: number;
    withdrawn_student_violations: number;
    resource_unavailability_violations: number;
    invalid_assignments: number;
    duration_violations: number;
  };
  violations: {
    type: string;
    severity: string;
    description: string;
    interview_id?: string;
  }[];
}

export interface DiffDetail {
  interview_id: string;
  student_id: string;
  student_name: string;
  company_id: string;
  company_name: string;
  change_type: 'UNCHANGED' | 'MOVED' | 'CANCELLED' | 'NEWLY_SCHEDULED';
  changes?: string[];
  change_label?: string;
  old?: {
    day?: number;
    time_str?: string;
    room_name?: string;
    panel_name?: string;
    status?: string;
    refusal_reason?: string;
  };
  new?: {
    day?: number;
    time_str?: string;
    room_name?: string;
    panel_name?: string;
    status?: string;
    refusal_reason?: string;
  };
  reason?: string;
}

export interface DiffResponse {
  old_version_id: number;
  new_version_id: number;
  summary: {
    unchanged: number;
    moved: number;
    cancelled: number;
    newly_scheduled: number;
    room_changes: number;
    panel_changes: number;
    time_changes: number;
    day_changes: number;
    replan_churn_pct: number;
    previously_scheduled: number;
  };
  diff_details: DiffDetail[];
}

export interface Notification {
  id: number;
  recipient_role: string;
  recipient_id: string;
  title: string;
  message: string;
  timestamp: string;
}

export interface DashboardResponse {
  active_version_id: number;
  active_version_summary: string;
  active_version_trigger: string;
  total_companies: number;
  total_students: number;
  total_rooms: number;
  metrics: Metrics;
  validation: ValidationReport;
  versions: ScheduleVersion[];
}
