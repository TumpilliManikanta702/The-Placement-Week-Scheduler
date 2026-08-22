import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import (
    Company, Student, Room, Panel, Shortlist, Interview, ScheduleVersion, Disruption, Notification
)
from app.seed.generator import generate_placement_dataset
from app.optimization.solver import PlacementScheduler
from app.services.validator import ScheduleValidator
from app.services.replanner import ReplanningService
from app.services.diff_engine import DiffEngine
from app.services.metrics import MetricsEngine
from app.services.disruption import DisruptionSimulatorService
from app.schemas.schemas import DisruptionRequest

router = APIRouter(prefix="/api")

@router.post("/seed")
def seed_dataset(seed: int = 42, db: Session = Depends(get_db)):
    """Resets DB and generates deterministic realistic placement dataset."""
    res = generate_placement_dataset(db, seed=seed)
    return res

@router.post("/schedule/generate")
def generate_initial_schedule(db: Session = Depends(get_db)):
    """Solves initial placement week schedule using CP-SAT / Priority-Heuristic."""
    if db.query(Company).count() == 0:
        generate_placement_dataset(db, seed=42)

    # Clear any lingering replan versions > 1 to guarantee clean baseline
    db.query(Notification).filter(Notification.version_id > 1).delete()
    db.query(Interview).filter(Interview.version_id > 1).delete()
    db.query(Disruption).delete()
    db.query(ScheduleVersion).filter(ScheduleVersion.id > 1).delete()
    db.commit()
    
    scheduler = PlacementScheduler(db)
    res = scheduler.generate_initial_schedule(version_id=1)
    
    # Calculate metrics
    metrics = MetricsEngine.calculate_metrics(db, version_id=1)
    ver = db.query(ScheduleVersion).filter(ScheduleVersion.id == 1).first()
    if ver:
        ver.quality_score = metrics["quality_score"]
        ver.metrics_json = json.dumps(metrics)
        db.commit()

    return {**res, "metrics": metrics}

@router.get("/schedule/{version_id}")
def get_schedule(
    version_id: int,
    day: Optional[int] = Query(None),
    company_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    panel_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Fetches interviews for a schedule version with optional filtering."""
    query = db.query(Interview).filter(Interview.version_id == version_id)

    if day is not None:
        query = query.filter(Interview.day == day)
    if company_id:
        query = query.filter(Interview.company_id == company_id)
    if room_id:
        query = query.filter(Interview.room_id == room_id)
    if student_id:
        query = query.filter(Interview.student_id == student_id)
    if panel_id:
        query = query.filter(Interview.panel_id == panel_id)
    if status:
        query = query.filter(Interview.status == status)

    interviews = query.all()

    # Enrich with names
    students = {s.id: s.name for s in db.query(Student).all()}
    companies = {c.id: c.name for c in db.query(Company).all()}
    rooms = {r.id: r.name for r in db.query(Room).all()}

    results = []
    for iv in interviews:
        results.append({
            "id": iv.id,
            "version_id": iv.version_id,
            "student_id": iv.student_id,
            "student_name": students.get(iv.student_id, iv.student_id),
            "company_id": iv.company_id,
            "company_name": companies.get(iv.company_id, iv.company_id),
            "panel_id": iv.panel_id,
            "room_id": iv.room_id,
            "room_name": rooms.get(iv.room_id, iv.room_id) if iv.room_id else None,
            "day": iv.day,
            "start_minutes": iv.start_minutes,
            "end_minutes": iv.end_minutes,
            "status": iv.status,
            "priority": iv.priority,
            "change_reason": iv.change_reason,
            "refusal_reason": iv.refusal_reason
        })

    return {"version_id": version_id, "count": len(results), "interviews": results}

@router.post("/schedule/validate/{version_id}")
def validate_schedule(version_id: int, db: Session = Depends(get_db)):
    """Executes independent schedule validation report."""
    report = ScheduleValidator.validate_version(db, version_id)
    return report.to_dict()

@router.post("/replan")
def replan_schedule(req: DisruptionRequest, db: Session = Depends(get_db)):
    """Executes minimal disruption replanning for a single disruption."""
    latest_ver = db.query(ScheduleVersion).order_by(ScheduleVersion.id.desc()).first()
    parent_v_id = latest_ver.id if latest_ver else 1

    res = ReplanningService.apply_disruption_and_replan(
        db=db,
        parent_version_id=parent_v_id,
        disruption_type=req.disruption_type,
        payload=req.model_dump()
    )
    return res

@router.post("/replan/live-defense")
def trigger_live_defense_scenario(db: Session = Depends(get_db)):
    """Triggers composite Mirai Labs Live Defense Scenario cleanly starting from Version 1 baseline."""
    # 1. Reset ORM entity statuses back to clean baseline state
    for c in db.query(Company).all():
        c.arrival_status = "on_time"
        c.delay_hours = 0.0
        c.delay_day = None

    for p in db.query(Panel).all():
        p.status = "active"
        p.dropped_day = None
        p.dropped_time_mins = None

    for s in db.query(Student).all():
        s.is_withdrawn = False
        s.withdrawal_day = None
        s.withdrawal_time_mins = None

    for r in db.query(Room).all():
        r.status = "available"
        r.unavailable_intervals_json = "[]"

    # 2. Delete any existing replan records > v1
    db.query(Notification).filter(Notification.version_id > 1).delete()
    db.query(Interview).filter(Interview.version_id > 1).delete()
    db.query(Disruption).delete()
    db.query(ScheduleVersion).filter(ScheduleVersion.id > 1).delete()
    db.commit()

    # 3. Ensure baseline v1 exists
    v1 = db.query(ScheduleVersion).filter(ScheduleVersion.id == 1).first()
    if not v1:
        scheduler = PlacementScheduler(db)
        scheduler.generate_initial_schedule(version_id=1)

    # 4. Execute exact 3-step scenario producing v1 -> v2 -> v3 -> v4
    res = DisruptionSimulatorService.run_live_defense_scenario(db, parent_version_id=1)
    return res

@router.get("/diff/{new_version_id}/{old_version_id}")
def get_schedule_diff(new_version_id: int, old_version_id: int, db: Session = Depends(get_db)):
    """Computes schedule diff between old and new versions."""
    res = DiffEngine.compute_diff(db, old_version_id, new_version_id)
    return res

@router.get("/metrics/{version_id}")
def get_version_metrics(version_id: int, db: Session = Depends(get_db)):
    """Computes operational KPIs and schedule quality score."""
    ver = db.query(ScheduleVersion).filter(ScheduleVersion.id == version_id).first()
    parent_v_id = ver.parent_version_id if ver else None
    res = MetricsEngine.calculate_metrics(db, version_id, parent_v_id)
    return res

@router.get("/dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Returns overall placement coordinator dashboard summary."""
    latest_ver = db.query(ScheduleVersion).order_by(ScheduleVersion.id.desc()).first()
    version_id = latest_ver.id if latest_ver else 1

    # Ensure baseline initial schedule exists if DB is unseeded
    if db.query(Company).count() == 0 or db.query(ScheduleVersion).count() == 0:
        generate_placement_dataset(db, seed=42)
        scheduler = PlacementScheduler(db)
        scheduler.generate_initial_schedule(version_id=1)
        latest_ver = db.query(ScheduleVersion).filter(ScheduleVersion.id == 1).first()
        version_id = 1

    metrics = MetricsEngine.calculate_metrics(db, version_id, latest_ver.parent_version_id if latest_ver else None)
    val_report = ScheduleValidator.validate_version(db, version_id)

    versions = db.query(ScheduleVersion).order_by(ScheduleVersion.id.asc()).all()

    return {
        "active_version_id": version_id,
        "active_version_summary": latest_ver.summary if latest_ver else "Initial",
        "active_version_trigger": latest_ver.trigger_event if latest_ver else "Seed",
        "total_companies": db.query(Company).count(),
        "total_students": db.query(Student).count(),
        "total_rooms": db.query(Room).count(),
        "metrics": metrics,
        "validation": val_report.to_dict(),
        "versions": [
            {
                "id": v.id,
                "parent_id": v.parent_version_id,
                "trigger_event": v.trigger_event,
                "summary": v.summary,
                "quality_score": v.quality_score,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in versions
        ]
    }

@router.get("/students")
def get_students(
    search: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    min_cgpa: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Student)
    if search:
        query = query.filter(Student.name.ilike(f"%{search}%") | Student.id.ilike(f"%{search}%"))
    if branch:
        query = query.filter(Student.branch == branch)
    if min_cgpa:
        query = query.filter(Student.cgpa >= min_cgpa)

    students = query.all()
    return [{"id": s.id, "name": s.name, "branch": s.branch, "cgpa": s.cgpa, "status": s.placement_status, "is_withdrawn": s.is_withdrawn} for s in students]

@router.get("/students/{student_id}")
def get_student_details(student_id: str, version_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    stud = db.query(Student).filter(Student.id == student_id).first()
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")

    if not version_id:
        latest_ver = db.query(ScheduleVersion).order_by(ScheduleVersion.id.desc()).first()
        version_id = latest_ver.id if latest_ver else 1

    shortlists = db.query(Shortlist).filter(Shortlist.student_id == student_id).all()
    comp_ids = [sl.company_id for sl in shortlists]
    companies = {c.id: c.name for c in db.query(Company).filter(Company.id.in_(comp_ids)).all()}

    interviews = db.query(Interview).filter(
        Interview.version_id == version_id,
        Interview.student_id == student_id
    ).all()

    rooms = {r.id: r.name for r in db.query(Room).all()}

    iv_list = []
    for iv in interviews:
        iv_list.append({
            "id": iv.id,
            "company_id": iv.company_id,
            "company_name": companies.get(iv.company_id, iv.company_id),
            "day": iv.day,
            "start_minutes": iv.start_minutes,
            "end_minutes": iv.end_minutes,
            "room_id": iv.room_id,
            "room_name": rooms.get(iv.room_id) if iv.room_id else None,
            "panel_id": iv.panel_id,
            "status": iv.status,
            "change_reason": iv.change_reason,
            "refusal_reason": iv.refusal_reason
        })

    return {
        "student": {
            "id": stud.id,
            "name": stud.name,
            "branch": stud.branch,
            "cgpa": stud.cgpa,
            "is_withdrawn": stud.is_withdrawn
        },
        "shortlisted_companies": [{"id": c_id, "name": comp_name} for c_id, comp_name in companies.items()],
        "interviews": iv_list
    }

@router.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    comps = db.query(Company).all()
    results = []
    for c in comps:
        results.append({
            "id": c.id,
            "name": c.name,
            "priority_tier": c.priority_tier,
            "cgpa_cutoff": c.cgpa_cutoff,
            "eligible_branches": json.loads(c.eligible_branches),
            "panel_count": c.panel_count,
            "interview_duration": c.interview_duration,
            "placement_day": c.placement_day,
            "expected_shortlist_size": c.expected_shortlist_size,
            "company_type": c.company_type,
            "arrival_status": c.arrival_status,
            "delay_hours": c.delay_hours
        })
    return results

@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return [{
        "id": r.id,
        "name": r.name,
        "building": r.building,
        "floor": r.floor,
        "status": r.status,
        "unavailable_intervals": json.loads(r.unavailable_intervals_json or "[]")
    } for r in rooms]

@router.get("/panels")
def get_panels(db: Session = Depends(get_db)):
    panels = db.query(Panel).all()
    comps = {c.id: c.name for c in db.query(Company).all()}
    return [{
        "id": p.id,
        "company_id": p.company_id,
        "company_name": comps.get(p.company_id, p.company_id),
        "panel_number": p.panel_number,
        "status": p.status
    } for p in panels]

@router.get("/notifications/{version_id}")
def get_notifications(version_id: int, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.version_id == version_id).all()
    return [{
        "id": n.id,
        "recipient_role": n.recipient_role,
        "recipient_id": n.recipient_id,
        "title": n.title,
        "message": n.message,
        "timestamp": n.timestamp.isoformat() if n.timestamp else None
    } for n in notifs]
