import json
import random
import numpy as np
from sqlalchemy.orm import Session
from app.config import config
from app.database.models import Company, Student, Room, Panel, Shortlist, ScheduleVersion, Interview, Disruption, Notification, Base
from app.database.connection import engine

BRANCHES = ["CSE", "IT", "AI/ML", "ECE", "EEE", "Mechanical", "Civil"]
BRANCH_WEIGHTS = [0.25, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10]

BUILDINGS = ["Admin Block", "CS Department", "Main Academic Block", "Innovation Center"]

COMPANY_TEMPLATES = [
    # Day 1 - Mass Recruiters (Priority Tier 1, High Panels, 30m, Lower Cutoff, Large Shortlists)
    {"name": "TCS Digital", "tier": 1, "cutoff": 6.0, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE"], "panels": 5, "duration": 30, "day": 1, "shortlist": 160, "type": "Mass Recruiter"},
    {"name": "Infosys Power Programmer", "tier": 1, "cutoff": 6.5, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 4, "duration": 30, "day": 1, "shortlist": 140, "type": "Mass Recruiter"},
    {"name": "Wipro Turbo", "tier": 1, "cutoff": 6.0, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE", "Mechanical", "Civil"], "panels": 4, "duration": 30, "day": 1, "shortlist": 150, "type": "Mass Recruiter"},
    {"name": "Cognizant Next", "tier": 1, "cutoff": 6.2, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE"], "panels": 4, "duration": 30, "day": 1, "shortlist": 130, "type": "Mass Recruiter"},

    # Day 1 & Day 2 - Premium Tech (Priority Tier 1, High Cutoff, 45-60m, High Demand)
    {"name": "Google India", "tier": 1, "cutoff": 8.5, "branches": ["CSE", "IT", "AI/ML"], "panels": 3, "duration": 60, "day": 1, "shortlist": 45, "type": "Product Tech"},
    {"name": "Microsoft", "tier": 1, "cutoff": 8.2, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 3, "duration": 60, "day": 1, "shortlist": 55, "type": "Product Tech"},
    {"name": "Amazon", "tier": 1, "cutoff": 7.8, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 4, "duration": 45, "day": 1, "shortlist": 70, "type": "Product Tech"},
    {"name": "Uber India", "tier": 1, "cutoff": 8.5, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 60, "day": 1, "shortlist": 30, "type": "Product Tech"},
    {"name": "Atlassian", "tier": 1, "cutoff": 8.3, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 60, "day": 2, "shortlist": 35, "type": "Product Tech"},
    {"name": "Flipkart", "tier": 1, "cutoff": 7.5, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 3, "duration": 45, "day": 2, "shortlist": 60, "type": "Product Tech"},
    {"name": "Adobe", "tier": 1, "cutoff": 8.0, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 45, "day": 2, "shortlist": 40, "type": "Product Tech"},
    {"name": "Directi / Media.net", "tier": 1, "cutoff": 8.4, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 60, "day": 2, "shortlist": 25, "type": "Product Tech"},

    # Day 1 & Day 2 - Quant / Finance / Consulting (Priority Tier 1, High Cutoff, 60-90m)
    {"name": "Goldman Sachs", "tier": 1, "cutoff": 8.5, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE"], "panels": 2, "duration": 60, "day": 1, "shortlist": 35, "type": "Quant/Finance"},
    {"name": "Morgan Stanley", "tier": 1, "cutoff": 8.3, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 2, "duration": 60, "day": 2, "shortlist": 30, "type": "Quant/Finance"},
    {"name": "Tower Research Capital", "tier": 1, "cutoff": 9.0, "branches": ["CSE", "AI/ML"], "panels": 1, "duration": 90, "day": 1, "shortlist": 12, "type": "Quant/Finance"},
    {"name": "McKinsey & Company", "tier": 1, "cutoff": 8.7, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE", "Mechanical", "Civil"], "panels": 2, "duration": 60, "day": 2, "shortlist": 20, "type": "Consulting"},
    {"name": "Bain & Company", "tier": 1, "cutoff": 8.6, "branches": ["CSE", "IT", "AI/ML", "ECE", "EEE", "Mechanical", "Civil"], "panels": 2, "duration": 60, "day": 2, "shortlist": 20, "type": "Consulting"},

    # Day 2 & Day 3 - Core Engineering (Priority Tier 2, Moderate Cutoff, 45-60m)
    {"name": "Texas Instruments", "tier": 2, "cutoff": 7.5, "branches": ["ECE", "EEE"], "panels": 3, "duration": 45, "day": 2, "shortlist": 40, "type": "Core Engineering"},
    {"name": "Qualcomm", "tier": 2, "cutoff": 7.8, "branches": ["ECE", "EEE", "CSE"], "panels": 3, "duration": 45, "day": 2, "shortlist": 45, "type": "Core Engineering"},
    {"name": "Intel", "tier": 2, "cutoff": 7.5, "branches": ["ECE", "EEE", "CSE", "IT"], "panels": 3, "duration": 45, "day": 2, "shortlist": 50, "type": "Core Engineering"},
    {"name": "L&T Construction", "tier": 2, "cutoff": 6.5, "branches": ["Civil", "Mechanical", "EEE"], "panels": 3, "duration": 45, "day": 3, "shortlist": 60, "type": "Core Engineering"},
    {"name": "Tata Motors", "tier": 2, "cutoff": 6.8, "branches": ["Mechanical", "EEE", "ECE"], "panels": 3, "duration": 45, "day": 3, "shortlist": 55, "type": "Core Engineering"},
    {"name": "Bosch India", "tier": 2, "cutoff": 7.0, "branches": ["ECE", "EEE", "Mechanical"], "panels": 2, "duration": 45, "day": 3, "shortlist": 40, "type": "Core Engineering"},
    {"name": "Siemens", "tier": 2, "cutoff": 7.2, "branches": ["EEE", "ECE", "Mechanical"], "panels": 2, "duration": 45, "day": 3, "shortlist": 35, "type": "Core Engineering"},

    # Day 3 & Day 4 - Mid-tier Tech & Specialist (Priority Tier 2-3, 30-45m)
    {"name": "Zomato", "tier": 2, "cutoff": 7.5, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 45, "day": 3, "shortlist": 40, "type": "Specialist/Niche"},
    {"name": "Razorpay", "tier": 2, "cutoff": 7.6, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 45, "day": 3, "shortlist": 35, "type": "Specialist/Niche"},
    {"name": "BrowserStack", "tier": 2, "cutoff": 7.5, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 45, "day": 3, "shortlist": 30, "type": "Specialist/Niche"},
    {"name": "Cisco Systems", "tier": 2, "cutoff": 7.2, "branches": ["CSE", "IT", "ECE", "EEE"], "panels": 3, "duration": 45, "day": 3, "shortlist": 55, "type": "Product Tech"},
    {"name": "NVIDIA", "tier": 2, "cutoff": 8.0, "branches": ["CSE", "AI/ML", "ECE"], "panels": 2, "duration": 60, "day": 3, "shortlist": 30, "type": "Product Tech"},
    {"name": "Ather Energy", "tier": 3, "cutoff": 6.8, "branches": ["Mechanical", "EEE", "ECE"], "panels": 2, "duration": 45, "day": 4, "shortlist": 30, "type": "Specialist/Niche"},
    {"name": "PwC India", "tier": 3, "cutoff": 6.5, "branches": ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil"], "panels": 3, "duration": 30, "day": 4, "shortlist": 70, "type": "Consulting"},
    {"name": "Deloitte USI", "tier": 3, "cutoff": 6.5, "branches": ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil"], "panels": 3, "duration": 30, "day": 4, "shortlist": 75, "type": "Consulting"},
    {"name": "Oracle", "tier": 2, "cutoff": 7.4, "branches": ["CSE", "IT", "AI/ML"], "panels": 2, "duration": 45, "day": 4, "shortlist": 45, "type": "Product Tech"},
    {"name": "Samsung R&D", "tier": 2, "cutoff": 7.5, "branches": ["CSE", "IT", "AI/ML", "ECE"], "panels": 3, "duration": 45, "day": 4, "shortlist": 50, "type": "Product Tech"},
    {"name": "AMD India", "tier": 2, "cutoff": 7.6, "branches": ["ECE", "EEE", "CSE"], "panels": 2, "duration": 45, "day": 4, "shortlist": 30, "type": "Core Engineering"}
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Aditya", "Sneha", "Vikram", "Neha", "Rahul", "Kavya",
    "Siddharth", "Ishita", "Arjun", "Riya", "Varun", "Tanvi", "Karan", "Pooja", "Dev", "Meera",
    "Aman", "Shruti", "Nikhil", "Shreya", "Abhinav", "Divya", "Yash", "Anushka", "Harsh", "Simran",
    "Ritwik", "Swati", "Pranav", "Nisha", "Gaurav", "Preeti", "Saurabh", "Deepika", "Kunal", "Bhavna"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Kumar", "Singh", "Rao", "Nair", "Reddy", "Joshi",
    "Mehta", "Agarwal", "Bhasin", "Chatterjee", "Banerjee", "Deshmukh", "Kulkarni", "Iyer", "Menon", "Saxena"
]

def generate_placement_dataset(db: Session, seed: int = config.SEED):
    """
    Generates a realistic, deterministic placement dataset:
    - 35 Companies
    - 800 Students
    - 20 Rooms
    - Panels per company
    - Overlapping shortlists based on CGPA and branch eligibility
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1. Clear database tables cleanly via ORM to avoid SQLite schema locking
    db.query(Notification).delete()
    db.query(Interview).delete()
    db.query(Disruption).delete()
    db.query(ScheduleVersion).delete()
    db.query(Shortlist).delete()
    db.query(Panel).delete()
    db.query(Company).delete()
    db.query(Student).delete()
    db.query(Room).delete()
    db.commit()

    # 2. Create Rooms (20 total)
    rooms = []
    for i in range(1, config.NUM_ROOMS + 1):
        bldg = BUILDINGS[(i - 1) % len(BUILDINGS)]
        floor = ((i - 1) // 4) + 1
        room = Room(
            id=f"R{i:02d}",
            name=f"Room {i:02d} ({bldg})",
            building=bldg,
            floor=floor,
            capacity=1,
            status="available",
            unavailable_intervals_json="[]"
        )
        rooms.append(room)
        db.add(room)
    db.flush()

    # 3. Create Companies (35 total) & Panels
    companies = []
    panels = []

    for idx, tmpl in enumerate(COMPANY_TEMPLATES[:config.NUM_COMPANIES], start=1):
        comp_id = f"C{idx:02d}"
        company = Company(
            id=comp_id,
            name=tmpl["name"],
            priority_tier=tmpl["tier"],
            cgpa_cutoff=tmpl["cutoff"],
            eligible_branches=json.dumps(tmpl["branches"]),
            panel_count=tmpl["panels"],
            interview_duration=tmpl["duration"],
            placement_day=tmpl["day"],
            expected_shortlist_size=tmpl["shortlist"],
            company_type=tmpl["type"],
            arrival_status="on_time",
            delay_hours=0.0,
            delay_day=tmpl["day"]
        )
        companies.append(company)
        db.add(company)

        # Create panels for company
        for p_idx in range(1, tmpl["panels"] + 1):
            panel = Panel(
                id=f"{comp_id}-P{p_idx}",
                company_id=comp_id,
                panel_number=p_idx,
                status="active"
            )
            panels.append(panel)
            db.add(panel)
    db.flush()

    # 4. Create Students (800 total)
    students = []
    # Truncated normal CGPA distribution around mean 7.5, std 1.0, range [5.5, 10.0]
    cgpa_raw = np.random.normal(7.5, 1.0, config.NUM_STUDENTS)
    cgpa_clipped = np.clip(cgpa_raw, 5.5, 10.0)

    for i in range(1, config.NUM_STUDENTS + 1):
        student_id = f"S{i:03d}"
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        branch = np.random.choice(BRANCHES, p=BRANCH_WEIGHTS)
        cgpa = round(float(cgpa_clipped[i - 1]), 2)

        student = Student(
            id=student_id,
            name=f"{fn} {ln}",
            branch=branch,
            cgpa=cgpa,
            graduation_year=2026,
            placement_status="unplaced",
            is_withdrawn=False
        )
        students.append(student)
        db.add(student)
    db.flush()

    # 5. Create Realistic Overlapping Shortlists
    shortlists = []
    # Group companies by branch & cutoff for quick lookup
    company_obj_list = db.query(Company).all()

    for student in students:
        # Filter eligible companies
        eligible_comps = []
        for comp in company_obj_list:
            branches = json.loads(comp.eligible_branches)
            if student.branch in branches and student.cgpa >= comp.cgpa_cutoff:
                eligible_comps.append(comp)

        if not eligible_comps:
            # Fallback: grant 1 company with lowest cutoff in branch
            fallbacks = [c for c in company_obj_list if student.branch in json.loads(c.eligible_branches)]
            if fallbacks:
                eligible_comps = [min(fallbacks, key=lambda c: c.cgpa_cutoff)]

        # Determine shortlist count based on CGPA quantile
        # High CGPA (>8.5) -> 4 to 8 companies
        # Medium CGPA (7.0 - 8.5) -> 2 to 5 companies
        # Low CGPA (<7.0) -> 1 to 3 companies
        if student.cgpa >= 8.5:
            target_count = random.randint(4, 8)
        elif student.cgpa >= 7.2:
            target_count = random.randint(2, 5)
        else:
            target_count = random.randint(1, 3)

        # Higher tier / mass recruiters have higher chance
        weights = []
        for comp in eligible_comps:
            # Mass recruiters have high weight, tier 1 high CGPA has high weight
            w = comp.expected_shortlist_size
            if student.cgpa >= 8.5 and comp.priority_tier == 1:
                w *= 2.0
            weights.append(w)

        total_w = sum(weights)
        if total_w > 0:
            probs = [w / total_w for w in weights]
            num_to_select = min(len(eligible_comps), target_count)
            selected_comps = np.random.choice(
                eligible_comps, size=num_to_select, replace=False, p=probs
            )
            for c in selected_comps:
                shortlist = Shortlist(
                    student_id=student.id,
                    company_id=c.id,
                    priority=c.priority_tier
                )
                shortlists.append(shortlist)
                db.add(shortlist)

    # 6. Initialize Root Schedule Version
    initial_version = ScheduleVersion(
        id=1,
        parent_version_id=None,
        trigger_event="Initial Seed & Reset",
        summary="Dataset generated with 35 companies, 800 students, 20 rooms.",
        quality_score=0.0,
        metrics_json="{}"
    )
    db.add(initial_version)
    db.commit()

    return {
        "status": "success",
        "companies": len(companies),
        "students": len(students),
        "rooms": len(rooms),
        "panels": len(panels),
        "shortlists": len(shortlists),
        "version_id": 1
    }
