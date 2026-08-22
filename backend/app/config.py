import os

class SystemConfig:
    # Scale parameters
    NUM_COMPANIES: int = 35
    NUM_STUDENTS: int = 800
    NUM_ROOMS: int = 20
    NUM_DAYS: int = 4
    
    # Time settings
    DAY_START_HOUR: int = 9       # 09:00 AM
    DAY_END_HOUR: int = 17       # 05:00 PM
    WORKING_MINUTES_PER_DAY: int = (DAY_END_HOUR - DAY_START_HOUR) * 60  # 480 mins
    SLOT_GRANULARITY_MINS: int = 15
    TOTAL_SLOTS_PER_DAY: int = WORKING_MINUTES_PER_DAY // SLOT_GRANULARITY_MINS  # 32 slots
    
    # Deterministic Seed & Environment Overrides
    SEED: int = int(os.getenv("SEED", "42"))
    
    # Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./placement_scheduler.db")
    
    # CORS Origins
    ALLOWED_ORIGINS: list = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

    # Objective & Penalty Weights
    WEIGHT_SCHEDULE_COVERAGE: float = 1000.0
    WEIGHT_PRIORITY_TIER_1: float = 300.0
    WEIGHT_PRIORITY_TIER_2: float = 200.0
    WEIGHT_PRIORITY_TIER_3: float = 100.0
    WEIGHT_MINIMIZE_STUDENT_WAIT: float = 2.0
    
    # Minimal Disruption Replanning Cost Matrix
    COST_UNCHANGED: float = 0.0
    COST_ROOM_CHANGE: float = 10.0
    COST_PANEL_CHANGE: float = 20.0
    COST_TIME_CHANGE_SAME_DAY: float = 50.0
    COST_TIME_CHANGE_PER_MIN: float = 1.0
    COST_DAY_CHANGE: float = 150.0
    COST_CANCEL: float = 500.0
    
    REPLAN_CHURN_THRESHOLD: float = float(os.getenv("REPLAN_CHURN_THRESHOLD", "0.15"))

config = SystemConfig()
