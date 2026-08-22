# MIRAI LABS — THE PLACEMENT WEEK SCHEDULER

A production-quality, constraint-optimized scheduling system and real-time operational coordinator dashboard built for Mirai Labs / Zutawa Studios.

The core capability of this application is:
> **Generate a realistic placement dataset → generate a feasible schedule → detect conflicts → handle real-world disruptions → minimally replan → clearly explain exactly what changed and why.**

---

## 🚀 Key Features

1. **Deterministic Realistic Dataset Generator (`SEED = 42`)**:
   - **35 Companies**: Categorized into Day-1 Mass Recruiters (TCS Digital, Infosys, Wipro), Premium Product Tech (Google, Microsoft, Amazon, Uber, Flipkart, Atlassian, Adobe), Quant/Finance/Consulting (Goldman Sachs, Morgan Stanley, McKinsey, Bain, Tower Research), Core Engineering (Texas Instruments, Qualcomm, Intel, L&T, Tata Motors, Bosch), and Specialist/Niche (Zomato, Razorpay, NVIDIA, Oracle).
   - **800 Students**: Realistic engineering branch distribution (CSE 25%, IT 15%, AI/ML 15%, ECE 15%, EEE 10%, Mech 10%, Civil 10%) and truncated normal CGPA distribution (5.5 - 10.0). High CGPA students are shortlisted by multiple companies, creating real-world schedule overlaps.
   - **20 Interview Rooms**: Schedulable campus resources across buildings.

2. **Genuine Google OR-Tools CP-SAT Solver & Priority Heuristic**:
   - **CP-SAT Solver Integration (`backend/app/optimization/`)**: Instantiates boolean decision variables (`model.NewBoolVar`), integer variables (`model.NewIntVar`), hard constraint clauses (`model.Add`, `model.AddBoolAnd`, `model.AddBoolOr`, `OnlyEnforceIf`), and an objective function (`model.Maximize`) using Google OR-Tools.
   - **11 Hard Constraints**: 0 student overlaps, 0 room overlaps, 0 panel overlaps, panel-company matching, working hours 09:00–17:00, arrival delays, withdrawn student checks.
   - **Unscheduled Interview Log**: Captures explicit refusal reasons (`no_compatible_room`, `no_available_panel`, `student_time_clash`, `company_arrival_delay`, `withdrawn_student`) and recommended actions.
   - **Independent Validator ([`validator.py`](file:///c:/Users/tumpi/OneDrive/Desktop/The Placement Week Scheduler/backend/app/services/validator.py))**: Standalone verification layer running after every generation/replan to guarantee 100% hard constraint compliance before UI render.

3. **Minimal-Disruption Replanning Engine ([`replanner.py`](file:///c:/Users/tumpi/OneDrive/Desktop/The Placement Week Scheduler/backend/app/services/replanner.py))**:
   - **Preserves Unaffected Schedules**: Freezes past/unaffected interviews.
   - **Cost Function Matrix**: Evaluates candidate placements against cost formula:
     $$\text{Cost} = 10 \cdot \text{RoomChange} + 20 \cdot \text{PanelChange} + 50 \cdot \text{TimeChange} + 1.0 \cdot |\Delta \text{mins}| + 150 \cdot \text{DayChange}$$
     Selects the candidate placement with the **minimum total cost**.
   - **Supports All 4 Disruption Types**: Company Delay, Panel Drop, Student Withdrawal, Room Unavailability.

4. **Live Defense Scenario Simulator & Clean Version Lineage**:
   - One-click trigger for the interviewer's disruption test: *Day-1 recruiter (TCS Digital) 3 hours late + 1 panel drop + 15 student withdrawals*.
   - Generates a clean version lineage: `v1 (Initial) -> v2 (Delay) -> v3 (Panel Drop) -> v4 (Withdrawals)`.

5. **Granular Schedule Diff Engine & Notification Center**:
   - Classifies every interview change into `UNCHANGED`, `MOVED` (time/room/panel/day), `CANCELLED`, `NEWLY_SCHEDULED`.
   - Calculates **Replan Churn %** ($\frac{\text{changed interviews}}{\text{previously scheduled interviews}} \times 100\%$).
   - Generates role-based notifications for Students, Companies, Panel Members, and Room Managers.

6. **Coordinator Dashboard SPA (React + TypeScript + Vite)**:
   - **Room / Time Gantt Grid Matrix**: Visual grid featuring 20 Room rows $\times$ 32 Time slot columns.
   - Top KPI cards, Conflict Center with urgent issue alerts, Student & Company directory inspectors, and Replan Diff modal.

---

## 🛠️ Technology Stack & Environment Configuration

- **Backend**: Python 3.12, FastAPI, Google OR-Tools CP-SAT, SQLAlchemy, SQLite, Pydantic v2, Pytest.
- **Frontend**: React 18, Vite, TypeScript, Lucide Icons, Glassmorphic Dark Mode Vanilla CSS.

### Configurable Environment Variables:

| Variable | Scope | Default Value | Description |
|---|---|---|---|
| `DATABASE_URL` | Backend | `sqlite:///./placement_scheduler.db` | SQLAlchemy database URL (SQLite local DB file or memory) |
| `ALLOWED_ORIGINS` | Backend | `*` | Comma-separated list of allowed CORS origin URLs |
| `PORT` | Backend | `8000` | FastAPI uvicorn server port |
| `HOST` | Backend | `0.0.0.0` | FastAPI uvicorn server host binding |
| `SEED` | Backend | `42` | Random seed for dataset generation |
| `REPLAN_CHURN_THRESHOLD` | Backend | `0.15` | High disruption warning threshold (15%) |
| `VITE_API_URL` | Frontend | `http://127.0.0.1:8000` | Base URL for FastAPI backend API endpoints |

---

## ⚙️ Local Development & Startup

### 1. Backend Startup (Fresh Database Auto-Initialization)
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Start FastAPI Uvicorn Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
> **Note**: On startup, if no database exists, FastAPI automatically initializes database schemas, seeds 35 companies, 800 students, 20 rooms, panels, shortlists, and generates the initial baseline schedule (`Version 1`).

Backend API docs available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Startup
```bash
cd frontend
# Install dependencies
npm install

# Start Vite Dev Server
npm run dev
```
Dashboard SPA available at `http://localhost:5173`.

---

## 📦 Production Deployment Guide

### Building Frontend Bundle
```bash
cd frontend
npm run build
```
Output static bundle will be generated in `frontend/dist/`.

### Recommended Deployment Topology
1. **Frontend Hosting**: Deploy static `frontend/dist/` bundle on **Vercel**, **Netlify**, or **AWS S3 + CloudFront**. Set build environment variable `VITE_API_URL=https://api.yourdomain.com`.
2. **Backend Hosting**: Deploy FastAPI application on **Render**, **Fly.io**, **Railway**, or **AWS EC2/App Runner** using Gunicorn/Uvicorn:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```
3. **Database**: Use persistent storage volume for SQLite (`/var/data/placement_scheduler.db`) or swap `DATABASE_URL` to managed PostgreSQL for multi-region scaling.

---

## 🧪 Automated Testing

Run the complete Pytest backend test suite (verifying generator, CP-SAT solver model, persistence visibility, cost math, version lineage, all 4 disruptions, and live defense scenario):

```bash
.\backend\venv\Scripts\python.exe -m pytest backend/tests/test_scheduler.py
```

---

## 📊 Live Defense Captured Scenario Telemetry

- **Initial Schedule (v1)**: 2,578 total shortlisted interviews, 1,107 scheduled, 89.30% room utilization, 0 conflicts.
- **Step 1: TCS Digital Delayed by 3h (v1 -> v2)**.
- **Step 2: TCS Digital Panel 1 Dropped (v2 -> v3)**.
- **Step 3: 15 Student Withdrawals (v3 -> v4)**.
- **Final Schedule (v4)**:
  - Total Evaluated Interviews: 2,578
  - Previously Scheduled: 1,099
  - Unchanged: 1,042 (**94.8% Preserved**)
  - Cancelled: 57
  - Newly Scheduled: 56
  - Replan Churn Rate: **5.19%**
  - Validation Result: **VALID PASS (0 hard-constraint violations)**
