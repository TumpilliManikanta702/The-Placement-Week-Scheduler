from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CompanySchema(BaseModel):
    id: str
    name: str
    priority_tier: int
    cgpa_cutoff: float
    eligible_branches: List[str]
    panel_count: int
    interview_duration: int
    placement_day: int
    expected_shortlist_size: int
    company_type: str
    arrival_status: str
    delay_hours: float

    class Config:
        from_attributes = True

class StudentSchema(BaseModel):
    id: str
    name: str
    branch: str
    cgpa: float
    graduation_year: int
    placement_status: str
    is_withdrawn: bool

    class Config:
        from_attributes = True

class RoomSchema(BaseModel):
    id: str
    name: str
    building: str
    floor: int
    capacity: int
    status: str
    unavailable_intervals: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class PanelSchema(BaseModel):
    id: str
    company_id: str
    panel_number: int
    status: str

    class Config:
        from_attributes = True

class InterviewSchema(BaseModel):
    id: str
    version_id: int
    student_id: str
    company_id: str
    panel_id: Optional[str] = None
    room_id: Optional[str] = None
    day: Optional[int] = None
    start_minutes: Optional[int] = None
    end_minutes: Optional[int] = None
    status: str
    priority: int
    change_reason: Optional[str] = None
    refusal_reason: Optional[str] = None

    class Config:
        from_attributes = True

class DisruptionRequest(BaseModel):
    disruption_type: str  # company_delay, panel_drop, student_withdrawal, room_unavailable
    company_id: Optional[str] = None
    delay_hours: Optional[float] = 2.0
    panel_id: Optional[str] = None
    student_id: Optional[str] = None
    room_id: Optional[str] = None
    effective_day: Optional[int] = 1
    effective_time_mins: Optional[int] = 0
    start_mins: Optional[int] = 0
    end_mins: Optional[int] = 480
    reason: Optional[str] = "Operational Disruption"

class SeedResponse(BaseModel):
    status: str
    companies: int
    students: int
    rooms: int
    panels: int
    shortlists: int
    version_id: int

class ValidationResponse(BaseModel):
    is_valid: bool
    violations_count: int
    summary: Dict[str, int]
    violations: List[Dict[str, Any]]
