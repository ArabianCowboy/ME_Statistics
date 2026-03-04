# ME Statistics — Web Application Design Document

> **Date**: 2026-03-04
> **Author**: Director of Medication Error + Development Team
> **Status**: Approved via brainstorming session

## Overview

A web application for the Medication Error department staff to log their monthly report counts, track annual goals and short-term tasks, and visualize performance. The app features a warm, motivational coaching aesthetic — celebrating progress rather than monitoring compliance.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python — Flask |
| Templating | Jinja2 (server-side rendered) |
| Database | SQLite via SQLAlchemy |
| Auth | Flask-Login (session-based) |
| Frontend | HTML, CSS (vanilla), JavaScript |
| Charts | Chart.js (client-side) |
| Fonts | Nunito (headings) + Source Sans 3 (body) via Google Fonts |

**Architecture**: Server-side rendered (SSR) for all pages. Dashboard statistics and charts fetched dynamically via `fetch()` against Flask JSON endpoints to avoid full page reloads.

---

## Data Model

### User
| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | Auto-increment |
| username | String, unique | Login credential |
| email | String, unique | For future use (notifications, password reset) |
| password_hash | String | Hashed with Werkzeug |
| full_name | String | Display name |
| role | String | `"admin"` or `"staff"` |
| monthly_target | Integer | Individual target set by admin |
| is_approved | Boolean | `False` until admin approves self-registration |
| created_at | DateTime | Auto-set |

### Goal (Annual / Long-term)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| title | String | Goal description |
| kpi | String | Key performance indicator |
| status | String | `"Not Started"` / `"In Progress"` / `"Completed"` |
| progress | Integer | 0–100% |
| priority | String | `"High"` / `"Medium"` / `"Low"` |
| comments | Text | Optional notes |
| user_id | Integer, FK → User | Owner |
| created_by | String | `"admin"` or `"self"` — tracks origin |
| created_at | DateTime | |

### Task (Short-term / Ad-hoc)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| description | String | Task description |
| status | String | `"Not Started"` / `"In Progress"` / `"Completed"` |
| progress | Integer | 0–100% |
| priority | String | `"High"` / `"Medium"` / `"Low"` |
| comments | Text | Optional notes |
| user_id | Integer, FK → User | Assigned staff member |
| created_at | DateTime | |

### MonthlyReport (SDR)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| user_id | Integer, FK → User | Staff member |
| year | Integer | e.g., 2026 |
| month | Integer | 1–12 |
| report_count | Integer | Total ME reports processed that month |
| created_at | DateTime | |
| *unique constraint* | | One entry per user/year/month |

### Key Design Decisions
- **Team goals**: When admin creates a "team goal," a copy is created for each staff member. Each person tracks their own progress independently.
- **No approval workflow**: Staff can create and update personal goals/tasks freely. Admin can see everything on their dashboard.
- **Individual targets**: Each staff member has their own `monthly_target` set by admin.

---

## User Roles & Authentication

### Two Roles
| Role | Access |
|------|--------|
| **Staff** | Own dashboard, own goals/tasks/reports, anonymized leaderboard |
| **Admin** | Everything staff can do, plus: all staff data, comparison charts, user management |

### Account Creation
1. **Self-registration**: Staff registers → account created with `is_approved=False` → admin approves → user can access the app
2. **Admin-created accounts**: Admin creates user directly → `is_approved=True` by default

### Auth Mechanics
- Password hashing: Werkzeug `generate_password_hash` / `check_password_hash`
- Session management: Flask-Login with `@login_required`
- Admin protection: Custom `@admin_required` decorator
- Unapproved users: See a "pending approval" message after login

---

## Pages & Routes

### Public
| Route | Page | Purpose |
|-------|------|---------|
| `/login` | Login | Username + password |
| `/register` | Register | Self-registration (pending approval) |

### Staff
| Route | Page | Purpose |
|-------|------|---------|
| `/dashboard` | Dashboard | Monthly trend chart, anonymized leaderboard, summary stats |
| `/goals` | My Goals | View/add/edit annual goals |
| `/tasks` | My Tasks | View/add/edit short-term tasks |
| `/reports` | Log Report | Submit monthly report count |
| `/profile` | Profile | View/update own info |

### Admin
| Route | Page | Purpose |
|-------|------|---------|
| `/admin/dashboard` | Admin Dashboard | Full leaderboard, comparison charts, team overview |
| `/admin/users` | Manage Users | Approve registrations, create users, set targets |
| `/admin/goals` | Staff Goals | View/create/edit goals for any staff member |
| `/admin/tasks` | Staff Tasks | View/create/edit tasks for any staff member |
| `/admin/reports` | Staff Reports | View/edit report logs for any staff member |

### Dashboard API Endpoints (for `fetch()`)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/my-stats` | GET | Staff's own monthly data + target |
| `/api/leaderboard` | GET | Anonymized for staff, full names for admin |
| `/api/compare?users=1,3,5` | GET | Admin: comparison data for selected staff |

---

## Project File Structure

```
ME_Statistics/
├── app.py                  # Flask app, config, ALL routes
├── models.py               # All SQLAlchemy models
├── templates/
│   ├── base.html           # Shared layout (sidebar + top bar + content area)
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── goals.html
│   ├── tasks.html
│   ├── reports.html
│   ├── admin_dashboard.html
│   ├── admin_users.html
│   ├── admin_goals.html
│   ├── admin_tasks.html
│   └── admin_reports.html
├── static/
│   ├── css/
│   │   └── style.css       # Complete design system
│   └── js/
│       └── app.js           # Charts + dashboard fetch()
├── requirements.txt
└── me_statistics.db         # SQLite (auto-created)
```

Semi-monolithic: 3 Python files, flat template folder, one CSS + one JS file.

---

## Visual Design System

### Design Direction
**Warm & Motivational** — a coaching dashboard that celebrates progress. Encouraging language, soft colors, approachable typography. This is NOT a surveillance tool.

### Color Palette
| Role | Hex | Usage |
|------|-----|-------|
| Primary | `#0D9488` (warm teal) | Sidebar active, buttons, links |
| Primary Light | `#5EEAD4` (soft mint) | Hover states, chart accents |
| Background | `#F9FAFB` (warm off-white) | Main content area |
| Sidebar | `#1E293B` (deep slate) | Sidebar background |
| Cards | `#FFFFFF` | Card backgrounds |
| Success | `#10B981` (encouraging green) | Above target |
| Warning | `#F59E0B` (gentle amber) | Below target — NOT red |
| Text Primary | `#1F2937` | Headings, body |
| Text Muted | `#6B7280` | Labels, secondary info |

> Amber instead of red for "below target" keeps the coaching feel.

### Typography
- **Headings**: Nunito — rounded, warm, professional
- **Body**: Source Sans 3 — clean, readable, healthcare-appropriate

### Layout
- **Sidebar** (left, 250px): Dark slate, navigation with icons + labels
- **Top bar** (horizontal, slim): Welcome message, role badge, logout
- **Content area**: Cards with `border-radius: 12px`, subtle shadows
- **Responsive**: Sidebar collapses to icons-only on tablets, hamburger toggle

### Dashboard Components

**Staff Dashboard:**
| Component | Details |
|-----------|---------|
| Summary Cards (3) | Reports this month, monthly target, goals in progress |
| Monthly Trend Chart | Bar chart, Jan–Dec, dashed target line |
| Anonymized Leaderboard | Rank, "You" highlighted, others as "Staff A/B/C" |

**Admin Dashboard:**
| Component | Details |
|-----------|---------|
| Summary Cards | Total staff, pending approvals, team reports this month |
| Full Leaderboard | Rank, real names, this month, YTD, target, % of target |
| Comparison Chart | Select 2-3 staff via checkboxes, overlay their trends |

### Micro-interactions
- Cards: subtle lift on hover (`translateY(-2px)`)
- Sidebar: smooth background transition on hover
- Progress bars: animated fill on page load
- Dashboard data: fade-in on `fetch()` load

### Encouraging Language
| Instead of… | Say… |
|-------------|------|
| "Reports: 42/50" | "You've completed 42 of 50 reports — almost there! 🎯" |
| "Below Target" | "A little more to go — you've got this!" |
| "Rank: 3/10" | "You're in the top 3 this month! 🌟" |

---

## Verification Plan

### Automated
- Test authentication (login, register, approval flow)
- Test role-based access (staff cannot reach `/admin/*`)
- Test CRUD operations for goals, tasks, reports
- Test unique constraint on MonthlyReport (one per user/month)
- Test leaderboard anonymization (staff API returns no real names)

### Manual
- Visual inspection of dashboard charts on desktop and tablet widths
- Verify encouraging language displays correctly based on data
- Confirm admin can create team goals that copy to all staff
- Verify sidebar collapse behavior on smaller screens
