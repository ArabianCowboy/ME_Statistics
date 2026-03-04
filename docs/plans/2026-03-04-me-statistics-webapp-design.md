# ME Statistics — Ultimate Combined Design Document

> **Date**: 2026-03-04
> **Version**: 2.0 (Combined from 4 independent plans)
> **Owner**: Director of Medication Error
> **Status**: Pending final approval

---

## 1. Overview

A web application for the Medication Error department staff to log monthly report counts, track annual goals and short-term tasks, and visualize performance. Features configurable approval workflows, bilingual support (EN/AR), anonymized leaderboards, and a warm motivational coaching aesthetic.

### Success Criteria
- Staff can log monthly report counts and track goals/tasks reliably
- Admin can manage users, set targets, and configure workflows per-user
- Dashboards accurately show trends, targets, and anonymized rankings
- All data mutations are captured in an immutable audit log
- Full English/Arabic support with RTL/LTR switching

---

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.9+ / Flask | Web framework |
| **ORM** | SQLAlchemy | Database operations |
| **Database** | SQLite (WAL mode) | File-based, zero-config |
| **Auth** | Flask-Login | Session management |
| **Forms** | Flask-WTF / WTForms | Validation + CSRF |
| **Templating** | Jinja2 | Server-side rendering |
| **Frontend** | HTML5, CSS3 (vanilla), JS | UI |
| **Charts** | Chart.js | Data visualization |
| **Fonts** | Nunito + Source Sans 3 | Google Fonts |
| **i18n** | Flask-Babel (or custom) | EN/AR translation |
| **Deployment** | Gunicorn + Nginx | Production server |

---

## 3. Architecture

**Modular Monolith** — Flask app with 4 Blueprints. One process, one database, server-rendered templates. JavaScript only for charts and dashboard `fetch()` calls.

### 3.1 Blueprints

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `auth` | `/auth` | Login, register, logout |
| `dashboard` | `/dashboard` | Staff + admin dashboards, API endpoints |
| `logs` | `/logs` | Monthly reports, goals, tasks CRUD |
| `users` | `/users` | Admin user management, settings |

### 3.2 Project Structure

```
ME_Statistics/
├── app/
│   ├── __init__.py              # App factory, config, blueprint registration
│   ├── config.py                # Environment settings
│   ├── extensions.py            # db, login_manager, csrf, babel init
│   ├── models.py                # All SQLAlchemy models
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py            # Login, register, logout
│   │   ├── forms.py             # Login/Register forms
│   │   └── decorators.py        # @login_required, @admin_required, @active_required
│   │
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── routes.py            # Staff dashboard, admin dashboard
│   │   └── services.py          # Metrics, trends, leaderboard calculations
│   │
│   ├── logs/
│   │   ├── __init__.py
│   │   ├── routes.py            # Monthly reports, goals, tasks CRUD
│   │   └── forms.py             # Report/goal/task forms
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── routes.py            # User management, admin settings
│   │   └── forms.py             # User create/edit forms
│   │
│   ├── templates/
│   │   ├── base.html            # Layout: sidebar + topbar + content
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── dashboard/
│   │   │   ├── staff.html
│   │   │   └── admin.html
│   │   ├── logs/
│   │   │   ├── reports.html
│   │   │   ├── goals.html
│   │   │   └── tasks.html
│   │   ├── users/
│   │   │   ├── manage.html
│   │   │   └── settings.html
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   │
│   └── translations/            # i18n files (EN/AR)
│       ├── en/
│       └── ar/
│
├── migrations/                  # Flask-Migrate
├── scripts/
│   └── create_admin.py          # Initial admin seeding
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt
├── run.py                       # Entry point
├── .env                         # Environment variables
└── README.md
```

---

## 4. Data Model

### 4.1 User

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | Auto-increment |
| username | String(80), unique | Login credential |
| email | String(120), unique | Future use (notifications, password reset) |
| password_hash | String(255) | bcrypt hashed |
| full_name | String(120) | Display name |
| role | Enum(`admin`, `user`) | Two roles |
| preferred_lang | Enum(`en`, `ar`) | Default `en` |
| monthly_target | Integer | Individual target set by admin |
| is_active | Boolean | Soft delete (default `True`) |
| is_approved | Boolean | Registration approval (default `False`) |
| goal_approval_required | Boolean | Per-user toggle (default `True`) |
| report_approval_required | Boolean | Per-user toggle (default `False`) |
| can_create_goals | Boolean | Per-user toggle (default `True`) |
| created_at | DateTime | Auto-set |
| updated_at | DateTime | Auto-updated |

### 4.2 Goal (Annual / Long-term)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| title | String | Goal description |
| kpi | String | Key performance indicator |
| status | Enum | `not_started`, `in_progress`, `completed` |
| progress | Integer | 0–100% |
| priority | Enum | `high`, `medium`, `low` |
| comments | Text | Optional notes |
| approval_status | Enum | `approved`, `pending`, `rejected` |
| user_id | Integer, FK → User | Owner |
| created_by_user_id | Integer, FK → User | Who created it (admin or self) |
| created_at | DateTime | |
| updated_at | DateTime | |

### 4.3 Task (Short-term / Ad-hoc)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| description | String | Task description |
| status | Enum | `not_started`, `in_progress`, `completed` |
| progress | Integer | 0–100% |
| priority | Enum | `high`, `medium`, `low` |
| comments | Text | Optional notes |
| user_id | Integer, FK → User | Assigned staff member |
| created_at | DateTime | |
| updated_at | DateTime | |

### 4.4 MonthlyReport (SDR)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| user_id | Integer, FK → User | Staff member |
| year | Integer | e.g., 2026 |
| month | Integer | 1–12 |
| report_count | Integer | Total ME reports processed |
| target_snapshot | Integer | User's target at time of creation |
| notes | Text | Optional |
| approval_status | Enum | `approved`, `pending` (if approval required) |
| created_at | DateTime | |
| updated_at | DateTime | |
| *unique constraint* | | (`user_id`, `year`, `month`) |

### 4.5 AuditLog

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| actor_user_id | Integer, FK → User | Who made the change |
| target_user_id | Integer, FK → User, nullable | Who was affected |
| entity_type | String | `user`, `goal`, `task`, `monthly_report`, `system_config` |
| entity_id | Integer | ID of the changed record |
| action | String | `created`, `updated`, `deactivated`, etc. |
| before_json | Text | Snapshot before change |
| after_json | Text | Snapshot after change |
| created_at | DateTime | Immutable timestamp (Asia/Riyadh) |

### 4.6 SystemConfig

| Column | Type | Notes |
|--------|------|-------|
| id | Integer, PK | |
| key | String, unique | Setting name |
| value | String | Setting value |
| updated_at | DateTime | |
| updated_by | Integer, FK → User | Admin who changed it |

**Default settings:**

| Key | Default | Description |
|-----|---------|-------------|
| `fiscal_year_start` | `1` | Month number (1=Jan) |
| `default_language` | `en` | New user default |
| `allow_self_registration` | `true` | Registration toggle |
| `leaderboard_visible` | `true` | Show anonymized leaderboard to staff |
| `default_monthly_target` | `0` | Default for new users |
| `department_name` | `Medication Error` | Displayed in app header |

---

## 5. Roles & Access Matrix

| Permission | Staff | Admin |
|------------|:-----:|:-----:|
| Login/logout | ✅ | ✅ |
| View own dashboard (anonymized leaderboard) | ✅ | ✅ |
| Create/edit own monthly reports | ✅ | ✅ |
| Create/edit own goals (if `can_create_goals`) | ✅ | ✅ |
| Create/edit own tasks | ✅ | ✅ |
| View admin dashboard (full names, all data) | ❌ | ✅ |
| Compare staff performance | ❌ | ✅ |
| Manage user accounts | ❌ | ✅ |
| Edit any user's reports/goals/tasks | ❌ | ✅ |
| Approve pending goals/reports | ❌ | ✅ |
| Manage system settings | ❌ | ✅ |
| Change language (for self) | ✅ | ✅ |

**Guardrails:**
- Cannot deactivate yourself
- Cannot remove the last active admin
- Inactive users cannot log in
- Unapproved users see "pending approval" page after login

---

## 6. Authentication & Account Flow

```
Self-Register → is_approved=False → Admin approves → User can access app
                                       ↑
                          Admin can also create users directly (is_approved=True)
```

- **Password hashing**: bcrypt
- **Sessions**: Flask-Login, cookies: `HttpOnly`, `SameSite=Lax`, `Secure` (HTTPS)
- **CSRF**: Flask-WTF on all POST forms
- **Failed logins**: Logged to AuditLog
- **Soft delete**: `is_active=False` (user can't login, data preserved)

---

## 7. Configurable Approval Workflow

### Per-User Settings (managed by admin on user profile)

| Toggle | Effect when ON | Effect when OFF |
|--------|---------------|-----------------|
| `goal_approval_required` | Staff goals go to pending → admin approves | Goals saved directly |
| `report_approval_required` | Monthly reports go to pending → admin approves | Reports saved directly |
| `can_create_goals` | Staff can create their own goals | Only admin assigns goals |

### Admin Approval Queue
When approval is required, the admin dashboard shows a **pending items** section:
- Pending goals (with approve/reject buttons)
- Pending monthly reports (with approve/edit/reject)
- Count badge on sidebar navigation

---

## 8. Pages & Routes

### Public
| Route | Purpose |
|-------|---------|
| `GET/POST /auth/login` | Login |
| `GET/POST /auth/register` | Self-registration |
| `POST /auth/logout` | Logout |

### Staff
| Route | Purpose |
|-------|---------|
| `GET /dashboard` | Staff dashboard |
| `GET/POST /logs/reports` | View/submit monthly reports |
| `GET/POST /logs/goals` | View/add/edit goals |
| `GET/POST /logs/tasks` | View/add/edit tasks |
| `POST /i18n/set/<en\|ar>` | Switch language |

### Admin
| Route | Purpose |
|-------|---------|
| `GET /dashboard/admin` | Admin dashboard + approval queue |
| `GET/POST /users` | List/create users |
| `GET/POST /users/<id>/edit` | Edit user (profile + per-user toggles) |
| `POST /users/<id>/deactivate` | Soft delete |
| `POST /users/<id>/reactivate` | Restore |
| `POST /users/<id>/reset-password` | Reset password |
| `GET/POST /logs/<user_id>/reports` | Edit any user's reports |
| `GET/POST /logs/<user_id>/goals` | Edit any user's goals |
| `GET/POST /logs/<user_id>/tasks` | Edit any user's tasks |
| `POST /dashboard/approve/<type>/<id>` | Approve pending item |
| `GET/POST /users/settings` | System-wide settings |

### Dashboard API (for `fetch()`)
| Endpoint | Returns |
|----------|---------|
| `GET /api/my-stats?year=` | Staff's monthly data + target |
| `GET /api/leaderboard?year=` | Anonymized for staff, full for admin |
| `GET /api/compare?users=1,3&year=` | Admin: comparison data |

### System
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Uptime check |

---

## 9. Metric Formulas

All calculations use `Asia/Riyadh` timezone and fiscal year from `SystemConfig`.

| Metric | Formula |
|--------|---------|
| Target Gap | `report_count - target_snapshot` |
| Achievement % | `(report_count / target_snapshot) × 100` (or N/A if target=0) |
| MoM Delta | `current_month - previous_month` |
| MoM Delta % | `(delta / previous_month) × 100` (or N/A if prev=0) |
| YTD Total | Sum of all reports in the fiscal year |

Percentages rounded to 1 decimal place.

---

## 10. Visual Design System

### Design Direction
**Warm & Motivational** — a coaching dashboard that celebrates progress. Encouraging language, soft colors, approachable typography.

### Color Palette
| Role | Hex | Usage |
|------|-----|-------|
| Primary | `#0D9488` | Sidebar active, buttons, links |
| Primary Light | `#5EEAD4` | Hover, chart accents |
| Background | `#F9FAFB` | Main content area |
| Sidebar | `#1E293B` | Sidebar background |
| Cards | `#FFFFFF` | Card backgrounds |
| Success | `#10B981` | Above target |
| Warning | `#F59E0B` | Below target (amber, not red) |
| Text | `#1F2937` | Primary text |
| Muted | `#6B7280` | Secondary text |

### Typography
- **Headings**: Nunito (warm, rounded)
- **Body**: Source Sans 3 (clean, readable)
- Both support Arabic glyphs

### Layout
- **Sidebar** (left, 250px): Dark slate, icons + labels, collapses to icons on tablet
- **Top bar** (horizontal): Welcome message, language toggle (EN/AR), role badge, logout
- **Content**: Cards with `border-radius: 12px`, subtle shadows
- **RTL**: Full mirror layout when Arabic is selected (`dir="rtl"`)

### Encouraging Language (Bilingual)
| Context | English | Arabic |
|---------|---------|--------|
| Near target | "Almost there! 🎯" | "!أوشكت على الوصول 🎯" |
| Above target | "Outstanding work! 🌟" | "!عمل رائع 🌟" |
| Below target | "You've got this! 💪" | "!يمكنك فعلها 💪" |
| Top 3 | "Top 3 this month!" | "!من الأوائل هذا الشهر" |

### Dashboard Components

**Staff Dashboard:**
- 3 summary cards (reports/target/goals)
- Monthly trend bar chart with target line (Chart.js)
- Anonymized leaderboard ("You" highlighted, others as "Staff A/B/C")

**Admin Dashboard:**
- Summary cards (total staff, pending approvals, team reports)
- Approval queue (if any pending items)
- Full leaderboard with real names
- Comparison chart (select staff via checkboxes)

---

## 11. Bilingual & RTL Support

- `lang` and `dir` set at `<html>` tag level
- Language toggle in top bar
- User preference saved in `preferred_lang`
- All static UI text from translation keys
- Sidebar mirrors to right side in RTL
- Charts remain LTR (Chart.js standard)

---

## 12. Security Baseline

- Password hashing: bcrypt
- CSRF: Flask-WTF tokens on all forms
- Session cookies: `HttpOnly`, `SameSite=Lax`, `Secure`
- Server-side role checks on all protected routes
- Input validation: WTForms server-side
- Audit: All mutations → AuditLog (append-only)
- Failed login logging

---

## 13. Deployment & Operations

- **Runtime**: Flask behind Gunicorn + Nginx
- **Database**: SQLite in WAL mode
- **Backups**: Daily automated backup, 30-day retention
- **Timezone**: `Asia/Riyadh` for all timestamps
- **Health**: `/health` endpoint for uptime checks
- **Environment**: `.env` file (`SECRET_KEY`, `DATABASE_URL`, `TIMEZONE`)

---

## 14. Implementation Phases

### Phase 1: Foundation
- Scaffold app structure, blueprints, extensions
- SQLAlchemy models + Flask-Migrate
- Auth (login/register/logout) + role decorators
- Seed initial admin

### Phase 2: Core Features
- Monthly report logging (CRUD + unique constraint)
- Goals + Tasks CRUD
- Admin user management (create/edit/deactivate/reactivate)
- Per-user workflow toggles

### Phase 3: Dashboards
- Staff dashboard (trend chart, anonymized leaderboard)
- Admin dashboard (full leaderboard, comparison chart)
- API endpoints for `fetch()`
- Approval queue (for users with approval enabled)

### Phase 4: Admin Settings & Polish
- System config page
- Target snapshots on MonthlyReport
- Encouraging language + motivational UX

### Phase 5: Bilingual & RTL
- Translation keys for all UI text
- EN/AR language files
- RTL layout mirroring
- Language toggle + user preference

### Phase 6: Audit, Testing & Deployment
- Full audit coverage on all mutations
- Test suite (unit, integration, e2e)
- Deployment config (Gunicorn, Nginx, backup scripts)
- Pilot readiness checklist

---

## 15. Post-V1 Backlog

- CSV/PDF export
- Email notifications / reminders for missing logs
- Month-lock / finalization workflow
- Advanced analytics / forecasting
- Historical Excel import tool
- Mobile-responsive PWA

---

## 16. Verification Plan

### Automated Tests
- Auth: login, register, approval flow, role decorators
- CRUD: goals, tasks, reports (create, edit, unique constraints)
- Access: staff cannot reach `/admin/*`, `/users/*`
- Leaderboard: staff API returns anonymized data only
- Audit: every mutation generates an AuditLog entry
- Approval: items with `pending` status don't appear in dashboards until approved
- i18n: pages render with correct `lang`/`dir` attributes

### Manual Verification
- Visual inspection of dashboard charts (desktop + tablet)
- RTL layout correctness in Arabic mode
- Encouraging language displays based on performance data
- Sidebar collapse on smaller screens
- Admin can toggle per-user workflow settings and see immediate effect
