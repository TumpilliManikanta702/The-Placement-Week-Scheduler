import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.seed.generator import generate_placement_dataset
from app.optimization.solver import PlacementScheduler
from app.optimization.model import PlacementCpSatModel
from app.services.validator import ScheduleValidator
from app.services.replanner import ReplanningService
from app.services.diff_engine import DiffEngine
from app.services.metrics import MetricsEngine
from app.services.disruption import DisruptionSimulatorService
from app.database.models import Company, Student, Room, Panel, Shortlist, Interview, ScheduleVersion

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_data_generation(db):
    res = generate_placement_dataset(db, seed=42)
    assert res["companies"] == 35
    assert res["students"] == 800
    assert res["rooms"] == 20
    assert res["shortlists"] > 1000

    students = db.query(Student).all()
    cgpas = [s.cgpa for s in students]
    avg_cgpa = sum(cgpas) / len(cgpas)
    assert 7.0 <= avg_cgpa <= 8.0

def test_initial_scheduling_and_cp_sat(db):
    generate_placement_dataset(db, seed=42)
    scheduler = PlacementScheduler(db)
    res = scheduler.generate_initial_schedule(version_id=1)

    assert res["scheduled_count"] > 0

    val_report = ScheduleValidator.validate_version(db, version_id=1)
    assert val_report.is_valid is True
    assert val_report.summary["student_conflicts"] == 0
    assert val_report.summary["room_conflicts"] == 0
    assert val_report.summary["panel_conflicts"] == 0

def test_cp_sat_model_invocation(db):
    """Verifies that OR-Tools CP-SAT model creates decision variables & hard constraints."""
    generate_placement_dataset(db, seed=42)
    companies = {c.id: c for c in db.query(Company).all()}
    students = {s.id: s for s in db.query(Student).all()}
    shortlists = db.query(Shortlist).all()
    rooms = db.query(Room).all()

    cp_model_obj = PlacementCpSatModel()
    variables = cp_model_obj.create_variables(
        shortlists=shortlists,
        companies=companies,
        students=students,
        rooms=rooms,
        panels_by_company={}
    )
    assert len(variables) == len(shortlists)

def test_replan_db_flush_and_diff_persistence(db):
    """
    PRIORITY 1 REGRESSION TEST:
    Verifies that replan flushes ORM additions so DiffEngine sees new records and total_evaluated > 0.
    """
    generate_placement_dataset(db, seed=42)
    scheduler = PlacementScheduler(db)
    scheduler.generate_initial_schedule(version_id=1)

    replan_res = ReplanningService.apply_disruption_and_replan(
        db=db,
        parent_version_id=1,
        disruption_type="company_delay",
        payload={"company_id": "C01", "delay_hours": 3.0, "effective_day": 1}
    )

    diff_summary = replan_res["diff_summary"]
    metrics = replan_res["metrics"]

    assert diff_summary["total_evaluated"] > 0
    assert diff_summary["previously_scheduled"] > 0
    assert metrics["scheduled_count"] > 0
    assert metrics["validation_passed"] is True

def test_version_lineage(db):
    """
    PRIORITY 2 REGRESSION TEST:
    Verifies clean version tree lineage: v1 -> v2 -> v3 -> v4.
    """
    generate_placement_dataset(db, seed=42)
    scheduler = PlacementScheduler(db)
    scheduler.generate_initial_schedule(version_id=1)

    scenario_res = DisruptionSimulatorService.run_live_defense_scenario(db, parent_version_id=1)
    
    v1 = db.query(ScheduleVersion).filter(ScheduleVersion.id == 1).first()
    v2 = db.query(ScheduleVersion).filter(ScheduleVersion.id == 2).first()
    v3 = db.query(ScheduleVersion).filter(ScheduleVersion.id == 3).first()
    v4 = db.query(ScheduleVersion).filter(ScheduleVersion.id == 4).first()

    assert v1 is not None and v1.parent_version_id is None
    assert v2 is not None and v2.parent_version_id == v1.id
    assert v3 is not None and v3.parent_version_id == v2.id
    assert v4 is not None and v4.parent_version_id == v3.id

def test_replan_candidate_cost_calculation(db):
    """
    PRIORITY 4 REGRESSION TEST:
    Verifies candidate placement penalty cost formula calculation.
    """
    old_iv = Interview(
        id="IV-1-0001",
        day=1,
        start_minutes=0,
        room_id="R01",
        panel_id="C01-P1"
    )

    # Same placement -> cost 0
    c0 = ReplanningService.calculate_candidate_cost(old_iv, day=1, start_mins=0, room_id="R01", panel_id="C01-P1")
    assert c0 == 0.0

    # Room change only -> cost 10
    c_room = ReplanningService.calculate_candidate_cost(old_iv, day=1, start_mins=0, room_id="R02", panel_id="C01-P1")
    assert c_room == 10.0

    # Panel change only -> cost 20
    c_panel = ReplanningService.calculate_candidate_cost(old_iv, day=1, start_mins=0, room_id="R01", panel_id="C01-P2")
    assert c_panel == 20.0

    # 30 min time shift -> cost 50 + 30 = 80
    c_time = ReplanningService.calculate_candidate_cost(old_iv, day=1, start_mins=30, room_id="R01", panel_id="C01-P1")
    assert c_time == 80.0

    # Day change -> cost 150
    c_day = ReplanningService.calculate_candidate_cost(old_iv, day=2, start_mins=0, room_id="R01", panel_id="C01-P1")
    assert c_day == 150.0

def test_all_disruptions_and_live_scenario(db):
    """
    PRIORITY 7 REGRESSION TEST:
    Verifies all 4 disruption types and composite live defense scenario.
    """
    generate_placement_dataset(db, seed=42)
    scheduler = PlacementScheduler(db)
    scheduler.generate_initial_schedule(version_id=1)

    scenario_res = DisruptionSimulatorService.run_live_defense_scenario(db, parent_version_id=1)
    final_v_id = scenario_res["final_version_id"]

    val_report = ScheduleValidator.validate_version(db, final_v_id)
    assert val_report.is_valid is True
    assert val_report.summary["student_conflicts"] == 0
    assert val_report.summary["room_conflicts"] == 0
    assert val_report.summary["panel_conflicts"] == 0
