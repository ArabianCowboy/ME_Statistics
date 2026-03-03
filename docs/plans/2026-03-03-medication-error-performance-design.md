# Medication Error Performance Web App - V1 Design

Date: 2026-03-03
Owner: Director of Medication Error
Status: Validated for implementation

## 1) Purpose and Success Criteria

Build a simple internal web application where staff log monthly work (number of reports plus KPI rows), then visualize performance over time.

Primary goals:
- Replace monthly manual spreadsheet tracking with structured, queryable data.
- Give regular users clear visibility into their own monthly progress.
- Give admins visibility across all staff and an easy way to compare month-over-month performance.
- Maintain accountability through full edit history.

Success criteria for v1:
- Staff can reliably create/update monthly logs.
- Admin can manage users and review cross-staff performance.
- Dashboards match expected calculations from sample spreadsheet logic.
- All write operations are audited.

## 2) Scope (YAGNI)

In scope for v1:
- Authentication and role-based authorization.
- Two roles: `user`, `admin`.
- Monthly logging by month/year dropdown (no submit/finalization workflow).
- Hybrid KPI input model: fixed KPI templates + optional custom KPI rows.
- User dashboard with trend and target comparison.
- Admin dashboard with table + basic line chart.
- Admin user management: add, edit, deactivate (soft delete).
- Bilingual UI from day one: English and Arabic with full RTL/LTR switching.
- Full immutable audit log for edits.

Out of scope for v1:
- Approval workflows.
- Notifications/reminders.
- Export/report generation.
- Forecasting/advanced analytics.

## 3) Architecture

Recommended architecture: modular monolith using Flask Blueprints.

Stack:
- Backend: Flask + SQLAlchemy.
- Database: SQLite.
- Frontend: server-rendered HTML (Jinja), CSS, JavaScript.
- Charts: Chart.js.

Rationale:
- Delivers quickly with low complexity.
- Keeps ownership simple for a small team.
- Preserves a clean path to future growth by adding modules, not services.

## 4) Modular Blueprint Structure

```text
app/
  __init__.py              # create_app(), blueprint registration
  extensions.py            # db, login/session tools, i18n setup
  models/
    __init__.py
    user.py
    monthly_log.py
    kpi_template.py
    kpi_entry.py
    audit_log.py
  auth/
    routes.py              # login/logout
    forms.py
    decorators.py          # role_required
    templates/auth/
  users/
    routes.py              # admin user CRUD + targets
    forms.py
    templates/users/
  dashboard/
    routes.py              # user/admin dashboards
    services.py            # metrics calculations
    templates/dashboard/
  i18n/
    service.py             # locale and direction helpers
  templates/
    base.html
  static/
```

Module boundaries:
- `auth`: identity, session, role gatekeeping.
- `users`: account lifecycle and admin user operations.
- `dashboard`: read-heavy analytics and charts.
- `models`: shared persistence layer.
- `i18n`: shared bilingual and RTL/LTR logic.

## 5) Authentication, Authorization, and Roles

Login identity:
- Username is a custom admin-defined unique value.

Access model:
- `user`: can create/edit own monthly logs and view own dashboard only.
- `admin`: can view all users, compare performance, and create/edit logs for any user.

Security requirements:
- Password hashing with a secure algorithm.
- Session-based auth with secure cookie settings.
- Server-side route protection for role checks.
- CSRF protection on all state-changing forms.

## 6) Bilingual and RTL/LTR Design

Languages:
- English and Arabic from v1.

Behavior:
- Full language toggle support.
- Full direction switching (`ltr` for English, `rtl` for Arabic).
- Templates use translation keys, not hardcoded mixed strings.

Placement:
- Locale selection and direction logic lives centrally in `app/i18n/service.py`.
- `base.html` applies `lang` and `dir` globally so all modules inherit correct behavior.

## 7) Data Model

### `User`
- `id`
- `username` (unique)
- `password_hash`
- `role` (`admin` or `user`)
- `is_active` (soft-delete flag)
- `preferred_lang` (`en`/`ar`)
- `monthly_target_reports` (integer)
- `created_at`, `updated_at`

### `MonthlyLog`
- `id`
- `user_id` (FK -> User)
- `year`, `month`
- `report_count` (integer >= 0)
- `notes`
- `created_at`, `updated_at`
- Unique constraint: (`user_id`, `year`, `month`)

### `KpiTemplate`
- `id`
- `title_en`, `title_ar`
- `is_active`
- `sort_order`

### `KpiEntry`
- `id`
- `monthly_log_id` (FK -> MonthlyLog)
- `template_id` (nullable FK -> KpiTemplate)
- `custom_title` (used when `template_id` is null)
- `status`
- `progress_percent` (0-100)
- `priority`
- `comments`

### `AuditLog`
- `id`
- `actor_user_id` (FK -> User)
- `target_user_id` (nullable FK -> User)
- `entity_type`
- `entity_id`
- `action` (create/update/deactivate/reactivate/reset_password/etc.)
- `before_json`
- `after_json`
- `created_at`

## 8) Key Data Flow

1. User logs in at `/auth/login`.
2. Session established; role controls route access.
3. User picks month/year and edits own monthly record at `/logs/me/edit`.
4. System upserts `MonthlyLog` and related `KpiEntry` rows.
5. Dashboard queries historical logs for trend calculations.
6. Admin can filter staff data and compare month-over-month in admin dashboard.
7. All mutations write an `AuditLog` record.

No submit/finalization state is used in v1; data is saved continuously and can be edited later.

## 9) Routes and Screens (v1)

Auth:
- `/auth/login`
- `/auth/logout`

User:
- `/dashboard/me?month=&year=`
- `/logs/me/edit?month=&year=`

Admin:
- `/dashboard/admin?month=&year=`
- `/users`
- `/users/new`
- `/users/<id>/edit`
- `/users/<id>/deactivate`
- `/users/<id>/reactivate`

Language:
- `/i18n/set-language/<en|ar>`

## 10) Admin User Lifecycle

Supported actions:
- Add user.
- Edit user profile/role/target/language.
- Deactivate user (soft delete).
- Reactivate user.
- Reset user password.

Delete policy:
- No hard delete in v1.
- Deactivation blocks login but keeps historical logs and audits intact.

Guardrails:
- Prevent deactivating current logged-in admin account.
- Prevent leaving system with zero active admins.

## 11) Error Handling

Validation and errors:
- Form-level validation for required fields and numeric bounds.
- 401/403 for auth/role violations.
- 404 for missing resources.
- 500 fallback page with generic bilingual message.

Data integrity:
- Unique monthly row per user/month/year.
- Safe handling for concurrent edits via latest-write + audit capture.

## 12) Testing Strategy

Unit tests:
- Auth checks, role decorators, password logic.
- Metrics calculation service (totals, deltas, target gap).
- i18n direction and locale selection.

Integration tests:
- Protected route access by role.
- Monthly log create/update paths.
- Admin user lifecycle actions and audit creation.

Functional tests:
- English/Arabic rendering with correct `dir` attributes.
- Dashboard trend correctness against seeded sample data.

## 13) Deployment and Operations

Deployment target:
- Flask behind Gunicorn and Nginx on one internal server/VM.

Configuration:
- `.env` for app secret and runtime settings.
- SQLite database file with scheduled backup.

Monitoring:
- Basic `/health` endpoint.
- Log failed logins and admin-level write actions.

## 14) Phased Implementation Plan

Phase 1: project skeleton, config, DB setup, auth base.
Phase 2: user management module and admin lifecycle.
Phase 3: monthly log entry (report count + hybrid KPI rows).
Phase 4: user dashboard and admin comparison dashboard.
Phase 5: i18n full bilingual + RTL/LTR hardening.
Phase 6: audit coverage, tests, pilot readiness.

This v1 design is intentionally simple, extensible, and aligned to departmental workflow.
