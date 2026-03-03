# Application Design: Medication Error Statistics Tracker

## Overview
A web application for the Medication Error staff to log their monthly report counts and update their progress on long-term goals. The application features a hybrid goal-setting approach, a robust approval workflow for progress updates, and a dual-perspective dashboard focusing on dynamic monthly targets.

## Objective
To build a web application that replaces the `Tasks and Goals.xlsx` spreadsheet. It will allow staff to track their monthly report numbers and progress on annual goals, while giving the Admin (Director of Medication Error) oversight, approval controls, and visual performance tracking.

## Key Files & Context
- Backend: Python (Flask or FastAPI recommended)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite via SQLAlchemy
- Target Directory: `/mnt/c/Users/midox/Desktop/AI_Project/ME_Statistics/`

## Data Model (SQLite & SQLAlchemy)
1.  **Users:** Stores credentials, roles (`admin`, `staff`), and the `dynamic_monthly_target` for report counts.
2.  **Goals:** Maps to "Section A: Goals & KPIs" and "Section B: Additional Tasks". Tracks `description`, `KPI`, `priority`, and overall `progress_percentage`.
3.  **Progress Logs:** A crucial table for the approval workflow. When a user updates a goal's progress or status, a record is created here with `status="pending"`. The main Goal record is only updated after Admin approval.
4.  **Monthly Reports:** Stores the single monthly report count entry per user, also subject to Admin approval.

## Workflows & Components

**1. Authentication & Authorization:**
*   Users log in with standard credentials.
*   Route protection ensures `staff` can only access their personal dashboard and submission forms, while `admin` has full access to oversight views and approval queues.

**2. Goal Management (Hybrid):**
*   Goals are long-term (e.g., annual).
*   Both Admin and Staff can propose or edit goals, but any changes or new goals require Admin approval before becoming "Active."

**3. Progress Updates & Approvals:**
*   Staff can log progress updates (percentage, status, comments) multiple times a month.
*   These updates enter an "Approval Queue" on the Admin dashboard.
*   Once approved, the main goal progress is updated, and the visualizations reflect the new data.

**4. Monthly Report Logging:**
*   Staff submit their total report count once a month.
*   This submission is compared against their specific `dynamic_monthly_target`.

## Dashboards & Visualization (HTML/CSS/JS)

**1. Staff Dashboard (The "Anonymized" View):**
*   **Personal Progress:** Visualizes their current progress on approved annual goals (e.g., progress bars).
*   **Report Target:** Shows their monthly report count vs. their dynamic target (e.g., a gauge or color-coded indicator).
*   **Anonymized Leaderboard:** Displays their rank relative to the team (e.g., "You are #3 out of 10") without revealing other staff members' names or specific metrics.

**2. Admin Dashboard (The "Complete" View):**
*   **Approval Queue:** A prominent section highlighting pending goal updates and monthly report submissions needing review.
*   **Team Heatmap:** A visual comparison of how far along *all* staff members are on their specific annual goals.
*   **Full Leaderboard:** A detailed view comparing raw report counts across the entire team, allowing for performance analysis.
*   **User Management:** Interface to set dynamic monthly targets and manage user accounts.

## Implementation Steps
1. Setup Python project environment (virtualenv) and install dependencies (Flask/FastAPI, SQLAlchemy, SQLite).
2. Initialize project structure (routes, templates, static, models).
3. Implement SQLAlchemy models (`User`, `Goal`, `ProgressLog`, `MonthlyReport`).
4. Build Authentication system (login, roles).
5. Develop Staff views (Dashboard, Add/Edit Goals, Add Progress, Submit Monthly Report).
6. Develop Admin views (Dashboard, Approval Queue, Full Leaderboard, User Management).
7. Implement approval logic (updating `Goal` based on approved `ProgressLog`).
8. Add visualization charts (Chart.js or similar) for both dashboards.

## Verification & Testing
1. Test authentication for both Admin and Staff roles.
2. Verify Staff cannot see other Staff's names/details on the leaderboard.
3. Test the hybrid goal creation flow (Staff proposes -> Admin approves).
4. Verify progress updates remain "pending" until Admin approval.
5. Check dynamic target logic on the dashboards.
