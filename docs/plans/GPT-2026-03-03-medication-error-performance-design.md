# Medication Error Performance Web App - V1 Product and Technical Design

Date: 2026-03-03
Last Updated: 2026-03-03
Owner: Director of Medication Error
Status: Approved baseline for implementation
Version: 1.1

## 1) Document Purpose

This document is the source of truth for v1 scope, behavior, and implementation boundaries.

Use this document to:
- Guide development decisions.
- Keep product behavior consistent across releases.
- Avoid scope creep while preserving future extensibility.

Any future change should update this file first, then implementation.

## 2) Product Goal and Success Criteria

Build a simple internal web app where staff record monthly work and performance is visualized over time.

Core outcome:
- Replace manual spreadsheet workflows with structured, auditable data.

Success criteria for v1:
- Staff can create and edit monthly records reliably.
- Admin can add/edit/deactivate users and manage monthly targets.
- Admin can review cross-staff performance using table + basic line chart.
- User dashboard accurately reflects report count, target comparison, and month-over-month trend.
- All write operations are captured in immutable audit history.

## 3) Product Principles (Keep It Simple)

- Build only what is required for monthly tracking and visibility.
- Prefer server-rendered pages over frontend complexity.
- Keep data model explicit and analytics-friendly.
- Enforce role permissions on the server, not only in UI.
- Preserve historical truth (soft delete, target snapshot, audit log).

## 4) Confirmed Decisions

- Architecture: modular monolith with Flask Blueprints.
- Tech stack: Flask, SQLAlchemy, SQLite, Jinja, HTML/CSS/JS, Chart.js.
- Auth identifier: custom username (admin-managed).
- Roles: `admin`, `user`.
- Workflow: no month submission/finalization; save by month/year and allow edits.
- Monthly input model: report count + hybrid KPI rows (fixed templates + custom rows).
- Main homepage metric: monthly report count.
- Target ownership: admin sets target per user.
- Delete policy: soft delete only (`is_active = false`).
- Bilingual: English + Arabic from day one.
- Direction: full RTL/LTR switching from day one.
- Audit: full before/after history for all writes.
- Dashboard default: hide deactivated users unless explicitly included.
- Timezone policy: `Asia/Riyadh` for month boundaries and timestamps.
- Historical import: out of scope for v1 (start fresh).

## 5) Scope (YAGNI)

In scope for v1:
- Authentication (login/logout) and role-based authorization.
- Admin user management (create, edit, deactivate, reactivate, reset password).
- Admin KPI template management (create, edit, deactivate, ordering).
- Monthly logs by month/year dropdown.
- User self-service edit for any month.
- Admin create/edit logs for any user and month.
- User dashboard with trends and target comparison.
- Admin dashboard with staff table and basic line chart.
- Full bilingual support and direction switching.
- Full immutable audit log for all data mutations.

Out of scope for v1:
- Approval workflow.
- Notifications/reminders.
- Export features (CSV/PDF).
- Forecasting/advanced predictive analytics.
- External integrations.

## 6) Architecture Overview

Recommended architecture: modular monolith with Flask Blueprints.

Why this is the right v1 choice:
- Low implementation overhead.
- Clear module boundaries without distributed complexity.
- Easy onboarding and maintenance for a small team.
- Straight path to add features as new modules later.

Runtime shape:
- One Flask app process.
- One SQLite database.
- Server-rendered templates for all screens.
- JavaScript only where needed (charts, minor UX interactions).

## 7) Code Structure

```text
app/
  __init__.py              # create_app, config loading, blueprint registration
  config.py                # environment-specific settings
  extensions.py            # db, migration, login/session, csrf, i18n extension

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
    decorators.py          # role_required, active_user_required
    services.py            # auth helpers
    templates/auth/

  users/
    routes.py              # admin user lifecycle operations
    forms.py
    services.py
    templates/users/

  kpis/
    routes.py              # admin KPI template lifecycle
    forms.py
    services.py
    templates/kpis/

  logs/
    routes.py              # user and admin monthly log edit flows
    forms.py
    services.py
    templates/logs/

  dashboard/
    routes.py              # user/admin dashboards
    services.py            # metrics and trend calculations
    templates/dashboard/

  i18n/
    service.py             # locale selection and direction helpers

  templates/
    base.html
    errors/
      403.html
      404.html
      500.html

  static/
    css/
    js/
```

## 8) Roles and Access Matrix

- `user` permissions:
  - Login/logout.
  - View own dashboard only.
  - Create/edit own logs for any month.
  - Add fixed/custom KPI rows to own log.

- `admin` permissions:
  - All `user` permissions.
  - View admin dashboard for all users.
  - Add/edit logs for any user.
  - Manage user accounts (create/edit/deactivate/reactivate/reset password).
  - Manage KPI templates.
  - Adjust monthly target snapshot for past records (audited).

Hard server-side rules:
- Every protected route checks authentication.
- Admin routes require `role == admin`.
- Inactive users cannot authenticate.

## 9) Functional Requirements

### 9.1 Authentication and Session

- Login with username + password.
- Logout destroys active session.
- Password stored only as hash.
- Failed login attempts are logged.
- Session cookie configured with secure flags.

### 9.2 User Management (Admin)

Supported actions:
- Create user with username, role, preferred language, monthly target, temporary password.
- Edit user profile/role/language/target.
- Reset password (no forced change in v1).
- Deactivate user (soft delete).
- Reactivate user.

Guardrails:
- Prevent deactivating currently logged-in admin.
- Prevent removing the last active admin.

### 9.3 KPI Template Management (Admin)

Templates are reusable fixed KPI definitions.

Supported actions:
- Create template with `title_en`, `title_ar`, sort order, active flag.
- Edit template fields.
- Deactivate template (not hard delete).
- Reorder template display.

Language fallback rule:
- At least one title is required.
- If one language title is missing, UI falls back to the available title.

### 9.4 Monthly Logging

Core behavior:
- User selects `month` and `year` from dropdown.
- System loads existing record or creates new one on first save.
- User enters `report_count`, optional notes, and KPI rows.

Hybrid KPI rows:
- Fixed rows from active templates.
- Optional custom rows created by user/admin.

Custom row carry-forward:
- Each custom row has a carry-forward toggle.
- If enabled, row is suggested in next month for same user.

Editing policy:
- Users can edit any month.
- Admin can edit any user and any month.
- Every change is audited.

### 9.5 User Dashboard

Default view emphasizes monthly report count.

Displays:
- Current month report count.
- Target vs actual and gap.
- Month-over-month change.
- Historical line trend.
- KPI row summary for selected month.

### 9.6 Admin Dashboard

Displays:
- Staff table for selected month/year.
- Basic line chart for trend comparison.
- Filters by month/year/user.
- Toggle to include deactivated users (default OFF).

Comparison emphasis:
- Primary comparison is each user vs their own historical months.

### 9.7 Bilingual and RTL/LTR

- Full English/Arabic support from v1.
- Global language toggle.
- `lang` and `dir` applied at layout root.
- All text from translation keys or bilingual fields.

## 10) Data Model Specification

### 10.1 `User`

Fields:
- `id` (PK)
- `username` (string, unique, required)
- `password_hash` (string, required)
- `role` (enum: `admin`, `user`, required)
- `is_active` (bool, default `true`)
- `preferred_lang` (enum: `en`, `ar`, default `en`)
- `monthly_target_reports` (int, >= 0, default `0`)
- `created_at` (datetime)
- `updated_at` (datetime)

Indexes and constraints:
- Unique index on `username`.

### 10.2 `MonthlyLog`

Fields:
- `id` (PK)
- `user_id` (FK -> `User.id`, required)
- `year` (int, required)
- `month` (int 1-12, required)
- `report_count` (int >= 0, required)
- `target_reports_snapshot` (int >= 0, required)
- `notes` (text, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

Rules:
- Unique constraint on (`user_id`, `year`, `month`).
- Snapshot is set from user target when month record is first created.
- Admin may adjust snapshot later; adjustment must be audited.

### 10.3 `KpiTemplate`

Fields:
- `id` (PK)
- `title_en` (string, optional)
- `title_ar` (string, optional)
- `is_active` (bool, default `true`)
- `sort_order` (int, default `0`)
- `created_at` (datetime)
- `updated_at` (datetime)

Rules:
- At least one of `title_en` or `title_ar` must be present.

### 10.4 `KpiEntry`

Fields:
- `id` (PK)
- `monthly_log_id` (FK -> `MonthlyLog.id`, required)
- `template_id` (nullable FK -> `KpiTemplate.id`)
- `custom_title` (string, nullable)
- `status` (enum: `not_started`, `in_progress`, `completed`, `blocked`)
- `progress_percent` (int 0-100)
- `priority` (enum: `low`, `medium`, `high`)
- `comments` (text, optional)
- `carry_forward` (bool, default `false`)
- `sort_order` (int, default `0`)
- `created_at` (datetime)
- `updated_at` (datetime)

Rules:
- If `template_id` is null, `custom_title` is required.
- If `template_id` is not null, `custom_title` is optional and ignored in display.

### 10.5 `AuditLog`

Fields:
- `id` (PK)
- `actor_user_id` (FK -> `User.id`, required)
- `target_user_id` (nullable FK -> `User.id`)
- `entity_type` (string, required)
- `entity_id` (int/string, required)
- `action` (string, required)
- `before_json` (json/text, optional)
- `after_json` (json/text, optional)
- `created_at` (datetime, required)

Examples of `action`:
- `user_created`, `user_updated`, `user_deactivated`, `user_reactivated`, `password_reset`
- `monthly_log_created`, `monthly_log_updated`, `target_snapshot_adjusted`
- `kpi_template_created`, `kpi_template_updated`, `kpi_template_deactivated`

## 11) Metric and Formula Definitions

All calculations use selected month/year and `Asia/Riyadh` time context.

- `actual_reports`: `MonthlyLog.report_count`
- `target_reports`: `MonthlyLog.target_reports_snapshot`
- `target_gap`: `actual_reports - target_reports`
- `achievement_percent`:
  - if `target_reports > 0`: `(actual_reports / target_reports) * 100`
  - else: `null` (display as `N/A`)
- `mom_delta`: `actual_reports(current_month) - actual_reports(previous_month)`
- `mom_delta_percent`:
  - if `previous_month > 0`: `(mom_delta / previous_month) * 100`
  - else: `null` (display as `N/A`)

Rounding:
- Percentages rounded to one decimal place.

## 12) Route and Screen Map

Auth:
- `GET /auth/login`
- `POST /auth/login`
- `POST /auth/logout`

Language:
- `POST /i18n/set-language/<en|ar>`

User self-service:
- `GET /dashboard/me?month=&year=`
- `GET /logs/me/edit?month=&year=`
- `POST /logs/me/edit?month=&year=`

Admin:
- `GET /dashboard/admin?month=&year=`
- `GET /users`
- `GET /users/new`
- `POST /users/new`
- `GET /users/<id>/edit`
- `POST /users/<id>/edit`
- `POST /users/<id>/deactivate`
- `POST /users/<id>/reactivate`
- `POST /users/<id>/reset-password`
- `GET /logs/<user_id>/edit?month=&year=`
- `POST /logs/<user_id>/edit?month=&year=`
- `GET /kpi-templates`
- `GET /kpi-templates/new`
- `POST /kpi-templates/new`
- `GET /kpi-templates/<id>/edit`
- `POST /kpi-templates/<id>/edit`
- `POST /kpi-templates/<id>/deactivate`

Ops:
- `GET /health`

## 13) Validation Rules

Common:
- All required fields validated server-side.
- Reject unknown enum values.
- Reject month outside 1-12.
- Reject negative integers for counts/targets.

Username:
- Unique.
- Trimmed.
- Case-normalized for comparison.

KPI entries:
- `progress_percent` must be between 0 and 100.
- Custom rows require `custom_title`.

## 14) Error Handling and UX Behavior

Expected HTTP behavior:
- 401: unauthenticated access to protected pages.
- 403: authenticated but unauthorized role.
- 404: unknown user/log/template.
- 500: unexpected server exception.

UX behavior:
- Show bilingual user-safe messages.
- Preserve form input on validation failure.
- Keep errors specific but not sensitive.

Concurrency behavior:
- v1 uses latest-write-wins.
- Every overwrite is auditable via `AuditLog`.

## 15) Security and Audit Requirements

Security baseline:
- Password hashing with secure algorithm.
- CSRF protection for all state-changing POST routes.
- Session cookie flags: `HttpOnly`, `SameSite=Lax`, `Secure` under HTTPS.
- Server-side authorization checks on all protected endpoints.

Audit baseline:
- All create/update/deactivate/reactivate/reset actions must write `AuditLog`.
- Audit includes actor, target, action, before, after, timestamp.
- Audit records are append-only.

## 16) Internationalization and Direction Rules

Locale source priority:
1. User explicit language switch (saved preference).
2. User profile `preferred_lang`.
3. App default `en`.

Direction rule:
- `en` -> `ltr`
- `ar` -> `rtl`

Template rule:
- Use translation keys for static UI text.
- For KPI titles, choose requested language first, then fallback title.

## 17) Non-Functional Requirements

- Reliability: no data loss on normal save operations.
- Performance: dashboard responses should feel immediate for expected department size.
- Maintainability: module boundaries remain clean and testable.
- Traceability: every sensitive write action is auditable.

## 18) Deployment and Operations

Deployment target:
- Flask app behind Gunicorn + Nginx on one internal server/VM.

Database operations:
- SQLite in WAL mode.
- Daily backup job.
- Backup retention policy (for example 30 days).
- Monthly restore drill to verify backup usability.

Environment configuration:
- `SECRET_KEY`
- `DATABASE_URL` (SQLite path)
- Session and CSRF settings
- Default locale/timezone

Observability:
- `/health` endpoint for uptime checks.
- Application logs for auth failures and admin writes.

Timezone:
- Use `Asia/Riyadh` for timestamps and month-boundary interpretation.

## 19) Testing Strategy

Unit tests:
- Password/auth helpers and role decorators.
- Metrics formulas and trend calculations.
- i18n locale and direction helpers.
- KPI entry validation and enum handling.

Integration tests:
- Route protection by role.
- User lifecycle actions and guardrails.
- Admin log editing for other users.
- KPI template lifecycle.
- Audit generation on all mutations.

Functional tests:
- English and Arabic render with correct `dir`.
- User monthly logging flow.
- Admin dashboard filtering and comparison.

Manual UAT checklist:
- Verify key calculations against known manual examples.
- Verify deactivated users cannot log in.
- Verify inactive-user filter behavior on admin dashboard.

## 20) Implementation Plan (Phased)

Phase 1: Foundation
- Scaffold app structure and extensions.
- Configure database migrations.
- Build auth basics and role decorators.
- Seed initial admin account.

Phase 2: User and KPI Admin Modules
- Build admin user lifecycle screens and routes.
- Add guardrails (self-deactivate and last-admin protection).
- Build KPI template CRUD/deactivate + ordering.

Phase 3: Monthly Logging Module
- Build month/year selector workflow.
- Implement monthly log upsert with `target_reports_snapshot`.
- Implement fixed + custom KPI rows with optional carry-forward.

Phase 4: Dashboards
- Build user dashboard metrics and trend line.
- Build admin table + basic line chart with filters.
- Default hide inactive users with include toggle.

Phase 5: Bilingual and RTL Hardening
- Wire translation keys across all pages.
- Apply global `lang` and `dir` behavior.
- Validate fallback behavior for partially translated KPI templates.

Phase 6: Audit, Stability, and Pilot Readiness
- Ensure full audit coverage on all writes.
- Complete test suite and bug fixes.
- Prepare deployment, backup job, and pilot checklist.

## 21) Post-V1 Backlog (Not in Current Scope)

- Export capabilities (CSV/PDF).
- Automated reminders for missing monthly logs.
- Approval/lock workflow for month closure.
- Advanced analytics and forecast views.
- Historical Excel import tool.

## 22) Acceptance Checklist (Go-Live)

- Auth and RBAC verified in production-like environment.
- User management and soft delete behavior verified.
- KPI template lifecycle verified.
- Monthly logging and edit-any-month behavior verified.
- User and admin dashboard metrics validated.
- English/Arabic + RTL/LTR verified.
- Audit completeness verified for all mutation paths.
- Backup and restore tested successfully.

This document intentionally balances clarity and simplicity so it can guide implementation now and remain useful for future enhancements.
