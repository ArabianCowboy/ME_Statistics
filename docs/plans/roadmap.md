# ME Statistics — Implementation Roadmap

> **Created**: 2026-03-04
> **Based on**: [Design Document v2.3](file:///c:/Users/Midoxp/Desktop/AI_Project/ME_Statistics/docs/plans/2026-03-04-me-statistics-webapp-design.md)
> **Status**: Ready to begin

---

## Quick Overview

The design document defines **6 phases**. This roadmap breaks each phase into concrete, actionable tasks with clear deliverables, estimated effort, and success criteria so you always know what to build next.

```
Phase 1: Foundation ──► Phase 2: Core Features ──► Phase 3: Dashboards
                                                         │
Phase 6: Audit & Deploy ◄── Phase 5: Bilingual ◄── Phase 4: Polish & Export
```

---

## 🏁 Milestone 1 — Foundation (Phase 1)

**Goal**: A running Flask app with authentication, database, and admin seeding.

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 1.1 | **Project scaffold** | `run.py`, `app/__init__.py` (factory), `config.py`, `extensions.py`, `requirements.txt` | 1 day |
| 1.2 | **SQLAlchemy models** | All 7 models (`User`, `Goal`, `Task`, `MonthlyReport`, `AuditLog`, `Notification`, `SystemConfig`) in `models.py` | 1 day |
| 1.3 | **Flask-Migrate setup** | Initial migration, SQLite in WAL mode | 0.5 day |
| 1.4 | **Auth blueprint** | `/auth/login`, `/auth/register`, `/auth/logout` routes + forms + bcrypt hashing | 1 day |
| 1.5 | **Role decorators** | `@login_required`, `@admin_required`, `@active_required` in `auth/decorators.py` | 0.5 day |
| 1.6 | **Admin seeder script** | `scripts/create_admin.py` — creates first admin account | 0.5 day |
| 1.7 | **Base template** | `base.html` with sidebar + topbar skeleton, Google Fonts loaded, design tokens in `style.css` | 1 day |
| 1.8 | **Login & Register pages** | Styled `login.html` and `register.html` using design system colors | 0.5 day |
| 1.9 | **Error pages** | `403.html`, `404.html`, `500.html` | 0.5 day |

**✅ Milestone 1 Complete When:**
- `python run.py` starts the app
- User can register → sees "pending approval" page
- Admin can log in via seeded account
- Database tables exist with correct schema
- Login/register pages match design system (warm teal palette, Plus Jakarta Sans font)

**⏱ Estimated Total: ~6 days**

---

## 🏁 Milestone 2 — Core Features (Phase 2)

**Goal**: Staff can log reports, manage goals/tasks. Admin can manage users.

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 2.1 | **Monthly Report CRUD** | `logs/routes.py` — create/edit/view reports with `(user_id, year, month)` unique constraint | 1 day |
| 2.2 | **Report forms** | `logs/forms.py` with WTForms validation | 0.5 day |
| 2.3 | **Goals CRUD** | Create/edit/view goals with status, priority, progress, approval_status | 1 day |
| 2.4 | **Tasks CRUD** | Create/edit/view tasks with status, priority, progress | 1 day |
| 2.5 | **Logs templates** | `reports.html`, `goals.html`, `tasks.html` — styled with design system | 1 day |
| 2.6 | **Admin user management** | `users/routes.py` — list, create, edit, deactivate, reactivate users | 1 day |
| 2.7 | **User forms** | `users/forms.py` — create/edit user forms with per-user toggles | 0.5 day |
| 2.8 | **Per-user workflow toggles** | `goal_approval_required`, `report_approval_required`, `can_create_goals` on edit user page | 0.5 day |
| 2.9 | **Admin guard rails** | Cannot deactivate self, cannot remove last admin, inactive users blocked | 0.5 day |
| 2.10 | **Users templates** | `manage.html`, `settings.html` — styled | 0.5 day |

**✅ Milestone 2 Complete When:**
- Staff can submit a monthly report (one per month enforced)
- Staff can create/edit goals and tasks
- Admin can create users, edit profiles, toggle per-user settings
- Deactivate/reactivate works with guardrails
- Approval-required goals show `pending` status

**⏱ Estimated Total: ~7 days**

---

## 🏁 Milestone 3 — Dashboards (Phase 3)

**Goal**: Interactive dashboards with charts, leaderboards, and approval queue.

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 3.1 | **Dashboard service layer** | `dashboard/services.py` — metrics, trends, leaderboard calculations using formulas from §9 | 1 day |
| 3.2 | **Dashboard API endpoints** | `/api/my-stats`, `/api/leaderboard`, `/api/compare` JSON endpoints | 1 day |
| 3.3 | **Staff dashboard page** | Hero card (teal bg), summary cards, Chart.js trend chart, anonymized leaderboard | 1.5 days |
| 3.4 | **Staff "You" row highlight** | Teal left border + glow on leaderboard for current user | 0.5 day |
| 3.5 | **Admin dashboard page** | Summary cards, full leaderboard with real names, comparison chart | 1.5 days |
| 3.6 | **Approval queue UI** | Pending goals/reports section on admin dashboard with approve/reject buttons | 1 day |
| 3.7 | **Chart.js integration** | `app.js` — bar chart with dashed target line, staggered fade-in animations | 1 day |
| 3.8 | **Encouraging messages** | Dynamic messages based on performance (Near/Above/Below target) per §10 | 0.5 day |

**✅ Milestone 3 Complete When:**
- Staff sees their trend chart and anonymized leaderboard
- Admin sees full data, comparison chart, and approval queue
- Approving/rejecting items from the queue works
- Encouraging messages display correctly based on data
- CSS animations: hover lift on cards, fade-in on load, animated progress bars

**⏱ Estimated Total: ~8 days**

---

## 🏁 Milestone 4 — Settings, Export, Notifications & Polish (Phase 4)

**Goal**: System config, data export, toast/bell notifications, and achievement celebrations.

### 4A — System Config & Export

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 4.1 | **System config page** | `users/settings.html` — admin can edit fiscal year, default language, registration toggle, etc. | 1 day |
| 4.2 | **Target snapshots** | `target_snapshot` auto-set on MonthlyReport creation | 0.5 day |
| 4.3 | **Export blueprint** | `export/__init__.py`, `routes.py` with period selection params | 0.5 day |
| 4.4 | **Excel generator** | `export/generators.py` — openpyxl builder for individual + team reports | 1.5 days |
| 4.5 | **PDF generator** | ReportLab builder — branded, color-coded, bilingual-ready | 1.5 days |
| 4.6 | **Export UI** | Export buttons on dashboards, period selector modal | 1 day |

### 4B — Notifications

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 4.7 | **Toast component** | CSS + JS toast system — success/warning/error/info with auto-dismiss, RTL-aware | 1 day |
| 4.8 | **Bell badge** | Topbar bell icon + count badge + dropdown list of notifications | 1 day |
| 4.9 | **Notification triggers** | Server-side: create Notification records on registration, approval, assignment events | 1 day |
| 4.10 | **Achievement toasts** | Gold-accented milestone celebrations (first report, target hit, streak) | 1 day |
| 4.11 | **Mark-as-read** | Click notification or "Mark all read" clears badge count | 0.5 day |

**✅ Milestone 4 Complete When:**
- Admin can configure system settings and changes take effect
- Staff can export their own data as Excel and PDF
- Admin can export any user's data and team summary
- Toast notifications appear on actions (save, error, etc.)
- Bell badge shows unread count, dropdown lists notifications
- Achievement toast fires on milestones with special gold styling

**⏱ Estimated Total: ~10 days**

---

## 🏁 Milestone 5 — Bilingual & RTL (Phase 5)

**Goal**: Full English/Arabic support with layout mirroring.

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 5.1 | **i18n setup** | Flask-Babel (or custom) configuration, `translations/` folder structure | 0.5 day |
| 5.2 | **Extract translation keys** | Replace all hardcoded UI text with `_()` calls | 1.5 days |
| 5.3 | **English translation file** | `translations/en/` complete | 0.5 day |
| 5.4 | **Arabic translation file** | `translations/ar/` complete — all labels, messages, encouraging text | 1 day |
| 5.5 | **Language toggle** | Topbar toggle saves to `preferred_lang`, sets `<html lang="" dir="">` | 0.5 day |
| 5.6 | **RTL CSS** | Sidebar mirrors to right, padding/margin flip, text alignment | 1 day |
| 5.7 | **RTL testing** | Visual QA of all pages in Arabic mode | 1 day |

**✅ Milestone 5 Complete When:**
- Toggle switches between EN/AR instantly
- All UI text renders in Arabic with Cairo font
- Sidebar moves to right side in RTL
- Toast notifications slide from correct direction
- Charts remain LTR per design spec
- User language preference persists across sessions

**⏱ Estimated Total: ~6 days**

---

## 🏁 Milestone 6 — Audit, Testing & Deployment (Phase 6)

**Goal**: Production-ready with full audit trail, tests, and deployment config.

| # | Task | Deliverable | Est. |
|---|------|-------------|------|
| 6.1 | **AuditLog coverage** | Service layer captures all mutations (user, goal, task, report, config changes) | 1.5 days |
| 6.2 | **Audit log viewer** | Admin page to browse audit trail (optional but recommended) | 1 day |
| 6.3 | **Unit tests** | Auth, CRUD, role checks, metric formulas | 2 days |
| 6.4 | **Integration tests** | Approval workflows, export correctness, notification triggers | 1.5 days |
| 6.5 | **E2E tests** | Full user journeys (register → approve → log → export) | 1.5 days |
| 6.6 | **Deployment config** | Gunicorn config, Nginx config, `.env.example`, `README.md` | 1 day |
| 6.7 | **Backup script** | Automated SQLite backup with 30-day retention | 0.5 day |
| 6.8 | **Health endpoint** | `GET /health` returns uptime status | 0.5 day |
| 6.9 | **Pilot readiness checklist** | Final QA pass, documentation review | 0.5 day |

**✅ Milestone 6 Complete When:**
- All CRUD operations generate audit log entries with before/after snapshots
- Test suite passes: unit + integration + e2e
- App runs behind Gunicorn with Nginx proxy
- Backup script works on schedule
- `/health` returns OK
- README has full setup + deployment instructions

**⏱ Estimated Total: ~10 days**

---

## 📊 Total Timeline Summary

| Milestone | Phase | Focus | Est. Days |
|-----------|-------|-------|-----------|
| **M1** | Foundation | Scaffold + Auth + DB | ~6 |
| **M2** | Core Features | Reports + Goals + Tasks + User mgmt | ~7 |
| **M3** | Dashboards | Charts + Leaderboards + Approvals | ~8 |
| **M4** | Polish & Export | Config + Export + Notifications | ~10 |
| **M5** | Bilingual & RTL | EN/AR + RTL layout | ~6 |
| **M6** | Audit & Deploy | Tests + Audit + Production | ~10 |
| | | **Total** | **~47 days** |

---

## 🚀 Recommended First Steps

You're currently at **Day 0** — design document complete, no code yet.

### This week, start with **Milestone 1 (Foundation)**:

1. **Task 1.1** — Create project scaffold (`run.py`, app factory, config, extensions, requirements.txt)
2. **Task 1.2** — Define all SQLAlchemy models in `models.py`
3. **Task 1.3** — Initialize Flask-Migrate, run first migration
4. **Task 1.7** — Build `base.html` layout + `style.css` design tokens (colors, fonts, shadows)

> [!TIP]
> Starting with the **models + base template** in parallel lets you see visual progress immediately while the data layer solidifies underneath.

### After Foundation is solid:
- Move to **Milestone 2** — the core CRUD features that make the app actually useful
- Each milestone builds cleanly on the previous one — no skipping!

---

## 📝 Notes

- Estimates assume a **single developer** working full-time
- Each milestone has a clear **"done when"** checklist — use these as your sprint acceptance criteria
- The design document is your **single source of truth** — refer back to it for every detail
- Post-V1 backlog items (emails, auto-refresh, PWA) are **out of scope** for this roadmap
