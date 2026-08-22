import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    priority_tier = Column(Integer, nullable=False)  # 1 = Day 1 Top, 2 = Premium, 3 = Core/Specialist
    cgpa_cutoff = Column(Float, nullable=False)
    eligible_branches = Column(Text, nullable=False)  # JSON list string e.g. ["CSE", "IT"]
    panel_count = Column(Integer, nullable=False)
    interview_duration = Column(Integer, nullable=False)  # Mins: 30, 45, 60, 90
    placement_day = Column(Integer, nullable=False)  # Preferred placement day 1..4
    expected_shortlist_size = Column(Integer, nullable=False)
    company_type = Column(String, nullable=False)  # Mass Recruiter, Product Tech, Core, Quant, Specialist
    arrival_status = Column(String, default="on_time")  # "on_time", "delayed"
    delay_hours = Column(Float, default=0.0)
    delay_day = Column(Integer, default=1)

    panels = relationship("Panel", back_populates="company", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="company", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="company")

class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    graduation_year = Column(Integer, default=2026)
    placement_status = Column(String, default="unplaced")  # "unplaced", "in_progress", "placed"
    is_withdrawn = Column(Boolean, default=False)
    withdrawal_day = Column(Integer, nullable=True)
    withdrawal_time_mins = Column(Integer, nullable=True)

    shortlists = relationship("Shortlist", back_populates="student", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="student")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    building = Column(String, nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, default=1)
    status = Column(String, default="available")  # "available", "unavailable"
    unavailable_intervals_json = Column(Text, default="[]")  # List of {day, start_mins, end_mins}

    interviews = relationship("Interview", back_populates="room")

class Panel(Base):
    __tablename__ = "panels"

    id = Column(String, primary_key=True, index=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    panel_number = Column(Integer, nullable=False)
    status = Column(String, default="active")  # "active", "dropped"
    dropped_day = Column(Integer, nullable=True)
    dropped_time_mins = Column(Integer, nullable=True)

    company = relationship("Company", back_populates="panels")
    interviews = relationship("Interview", back_populates="panel")

class Shortlist(Base):
    __tablename__ = "shortlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    priority = Column(Integer, default=1)

    student = relationship("Student", back_populates="shortlists")
    company = relationship("Company", back_populates="shortlists")

class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_version_id = Column(Integer, ForeignKey("schedule_versions.id"), nullable=True)
    trigger_event = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    quality_score = Column(Float, default=0.0)
    metrics_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    interviews = relationship("Interview", back_populates="version", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="version", cascade="all, delete-orphan")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("schedule_versions.id"), nullable=False)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    panel_id = Column(String, ForeignKey("panels.id"), nullable=True)
    room_id = Column(String, ForeignKey("rooms.id"), nullable=True)
    
    day = Column(Integer, nullable=True)  # 1..4
    start_minutes = Column(Integer, nullable=True)  # Mins from day start (0..480)
    end_minutes = Column(Integer, nullable=True)
    
    status = Column(String, nullable=False, default="scheduled")  # scheduled, completed, cancelled, withdrawn, rescheduled, unscheduled
    
    # Audit & Diff Tracking
    original_day = Column(Integer, nullable=True)
    original_start_minutes = Column(Integer, nullable=True)
    original_room_id = Column(String, nullable=True)
    original_panel_id = Column(String, nullable=True)
    
    reschedule_count = Column(Integer, default=0)
    priority = Column(Integer, default=1)
    change_reason = Column(String, nullable=True)
    refusal_reason = Column(String, nullable=True)

    version = relationship("ScheduleVersion", back_populates="interviews")
    student = relationship("Student", back_populates="interviews")
    company = relationship("Company", back_populates="interviews")
    panel = relationship("Panel", back_populates="interviews")
    room = relationship("Room", back_populates="interviews")

class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("schedule_versions.id"), nullable=True)
    disruption_type = Column(String, nullable=False)  # company_delay, panel_drop, student_withdrawal, room_unavailable
    payload_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("schedule_versions.id"), nullable=False)
    recipient_role = Column(String, nullable=False)  # Student, Company, Panel, Coordinator, RoomManager
    recipient_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    version = relationship("ScheduleVersion", back_populates="notifications")
