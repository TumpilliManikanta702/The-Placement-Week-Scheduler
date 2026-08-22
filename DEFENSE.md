# DEFENSE.MD — LIVE TECHNICAL INTERVIEW DEFENSE GUIDE

This document prepares you for the **Mirai Labs Live Defense Session**, where interviewers will inject real-world disruptions, ask technical architectural questions, and evaluate your algorithmic trade-offs.

---

## 🏛️ 1. ARCHITECTURE & SYSTEM DESIGN

### Q1: Why did you choose FastAPI for the backend?
**Answer**:
- **Performance & Async Capabilities**: FastAPI is built on Starlette and Pydantic, offering sub-millisecond API responses and asynchronous I/O support.
- **Type Safety & Auto Validation**: Pydantic models automatically validate incoming disruption payloads and format outgoing responses, preventing malformed data.
- **Auto Documentation**: Exposes OpenAPI/Swagger specs out of the box at `/docs`.

### Q2: Why did you choose React + Vite + TypeScript for the frontend?
**Answer**:
- **Sub-Second Component Rendering**: Placement coordinators work under extreme stress during disruptions. Vite provides instant HMR, while React's virtual DOM ensures real-time KPI and schedule timeline updates without full page reloads.
- **Strict Typing**: Shared TypeScript definitions (`types/index.ts`) eliminate API contract bugs between frontend and backend.

### Q3: Why SQLite initially? How would you scale the storage layer?
**Answer**:
- **Self-contained & Zero Latency**: SQLite provides ACID transactions with zero network overhead for take-home demonstration.
- **Production Migration**: The backend uses **SQLAlchemy ORM**. Swapping to PostgreSQL for production requires changing only 1 line in `config.py` (`DATABASE_URL = "postgresql://user:pass@localhost/db"`).

---

## 🧠 2. SCHEDULING ALGORITHM & CP-SAT SOLVER MODEL

### Q4: How is the initial schedule generated?
**Answer**:
- We implement a genuine **Google OR-Tools CP-SAT Constraint Programming Solver** (`backend/app/optimization/model.py`, `constraints.py`, `objective.py`, `solver.py`) paired with a deterministic **Priority Heuristic Fallback**.
- The CP-SAT model instantiates boolean decision variables (`model.NewBoolVar`), integer variables (`model.NewIntVar`), hard constraint clauses (`model.Add`, `model.AddBoolAnd`, `model.AddBoolOr`, `OnlyEnforceIf`), and an objective function (`model.Maximize`).
- Shortlist candidates are ordered by `(Company Priority Tier, Preferred Placement Day, -Student CGPA)`.
- Time is modeled in discrete 15-minute slot intervals (32 slots per day from 09:00 to 17:00).

### Q5: What are your Hard Constraints vs Soft Objectives?
**Hard Constraints (Must NEVER be violated)**:
1. No student overlap (a student cannot attend 2 interviews at the same time).
2. No room overlap (a room cannot host 2 interviews at the same time).
3. No panel overlap (a panel cannot conduct 2 interviews at the same time).
4. Panel-company binding (a panel can only interview for its company).
5. Student shortlist match (student must be shortlisted by company).
6. Working-hours bound (interviews must fit strictly inside 09:00 AM - 05:00 PM).
7. Duration adherence (30, 45, 60, 90 mins respected).
8. Unavailable rooms not used.
9. Dropped panels not used.
10. Withdrawn students not assigned new interviews.
11. Company arrival delay bound.

**Soft Objectives (Weighted Scoring & CP-SAT Maximization)**:
- $+1000$ per scheduled interview (Coverage maximization).
- $+300$ for Priority Tier 1 companies (Mass recruiters / Top Tech first).
- $+150$ for preferred placement day scheduling.
- $-2.0$ per minute of student idle wait time between same-day interviews.

### Q6: How do you guarantee the generated schedule has 0 conflicts?
**Answer**:
- We implemented a standalone **`ScheduleValidator`** service (`backend/app/services/validator.py`).
- After every generation or replan, `ScheduleValidator` independently scans all scheduled interviews and checks for student, room, panel, working hour, and resource availability overlaps.
- The UI displays a **"VALID SCHEDULE · 0 HARD-CONSTRAINT VIOLATIONS"** badge only when the validator confirms 0 violations.

---

## 🔄 3. MINIMAL-DISRUPTION REPLANNING ENGINE & COST FUNCTION

### Q7: Why NOT regenerate the schedule from scratch after a disruption?
**Answer**:
- In a real college placement week, hundreds of students and company executives have already received their time slots and room numbers.
- Regenerating from scratch causes **massive schedule churn**: a 2-hour delay for 1 company would reshuffle 300 unrelated interviews, causing chaos on campus.
- Our `ReplanningService` freezes unaffected interviews and evaluates candidate placements using a weighted cost penalty function.

### Q8: What is your Replanning Cost Matrix & Formula?
**Answer**:
Every candidate placement $(day, start\_mins, room\_id, panel\_id)$ is evaluated against:
$$\text{Cost} = 10 \cdot \text{is\_room\_changed} + 20 \cdot \text{is\_panel\_changed} + 50 \cdot \text{is\_time\_changed} + 1.0 \cdot |\Delta \text{mins}| + 150 \cdot \text{is\_day\_changed}$$
- Keep time/room/panel $\to$ Cost: 0
- Change room only $\to$ Cost: 10
- Change panel only $\to$ Cost: 20
- Shift time by 30 mins $\to$ Cost: $50 + 30 = 80$
- Change day $\to$ Cost: 150
- Cancel interview $\to$ Cost: 500

The replanner evaluates all feasible candidate placements and **selects the candidate with the minimum total cost**.

### Q9: How do you explain the Live Defense Scenario & Room Utilization Metrics?
**Answer**:
Our clean baseline Version 1 schedules 1,107 of the 2,578 shortlisted interviews and uses 34,290 room-minutes, giving 89.30% room utilization. The live defense then applies three sequential disruptions: TCS Digital is delayed by three hours, panel C01-P1 drops, and 15 students withdraw. The resulting Version 4 contains 1,099 scheduled interviews and uses 34,245 room-minutes, giving 89.18% room utilization.

Version 1 uses 34,290 room-minutes (89.30%). Version 4 uses 34,245 room-minutes (89.18%). The final change is a result of the complete schedule state after the sequential delay, panel-drop, and withdrawal replans. Between Version 2 and Version 3, scheduled interviews change from 1,107 to 1,099 due to the dropped panel, and remain stable at 1,099 in Version 4.

More importantly, the replanner preserves 1,040 of the 1,099 interviews that were scheduled in Version 3 immediately before the final replan, giving a 94.63% preservation rate (1,040 / 1,099). Only 59 prior scheduled interviews changed, producing 5.37% replan churn (59 / 1,099), while the independent validator reports zero hard-constraint violations.

---

## 🎲 4. DATASET REALISM

### Q10: How did you make the dataset realistic instead of uniform random?
**Answer**:
- **Correlations**: Higher CGPA students (e.g. > 8.5) meet more company CGPA cutoffs and have a higher probability of being shortlisted by 5-8 top companies. This introduces dense schedule overlap challenges.
- **Branch Eligibility**: Core engineering companies (Texas Instruments, L&T, Tata Motors) filter specifically for ECE, EEE, Mech, or Civil, while mass recruiters accept all branches.
- **Company Tiers**: Day-1 mass recruiters (TCS Digital, Infosys) have lower CGPA cutoffs (6.0), higher panel counts (4-5), and 30-min duration. Premium tech (Google, Microsoft) have higher cutoffs (8.0-8.5), 60-min duration, and smaller shortlists.

---

## 📈 5. SCALABILITY & PERFORMANCE

### Q11: How does your algorithm perform with 800 students? How would it scale to 10,000 students?
**Answer**:
- **Current Performance**: Initial scheduling for 800 students (~1,500 interviews) completes in ~0.5 seconds. Replanning completes in ~0.1 seconds.
- **Scaling to 10,000 Students**:
  - We would partition the schedule by **Placement Day** and **Department / Branch Clusters** (e.g., CS/IT block vs Mechanical/Civil block).
  - Use OR-Tools CP-SAT with parallel worker threads (`model.parameters.num_search_workers = 8`).
  - Pre-filter candidate search space using interval trees or spatial room indexing.
