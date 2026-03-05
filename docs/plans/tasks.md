# Project Milestones

> Note: Checked items indicate implementation completed in code. Full end-to-end verification is pending and will be completed in a dedicated testing phase.

## Milestone 1: Foundation
**Goal:** Establish the application foundation with core architecture, data model, authentication, and initial admin access.
**Done when:** The app scaffold, blueprints, extensions, SQLAlchemy models, and migrations are in place; login/register/logout with role decorators works; and an initial admin account can be seeded.
- [x] Scaffold app structure with blueprints and app factory.
- [x] Set up extensions (`db`, `login_manager`, `csrf`, `babel`) and configuration.
- [ ] Implement SQLAlchemy models and initialize Flask-Migrate.
- [x] Build authentication flow (login/register/logout) and role/access decorators.
- [x] Add script to seed the initial admin account.
- [ ] Generate and apply initial migration once Python package tooling is available in environment.

## Milestone 2: Core Features
**Goal:** Deliver the primary operational workflows for report logging, goals/tasks tracking, and admin user control.
**Done when:** Monthly reports, goals, and tasks are manageable via CRUD flows; monthly report uniqueness is enforced; admins can create/edit/deactivate/reactivate users; and per-user workflow toggles are available.
- [x] Implement monthly report CRUD with (`user_id`, `year`, `month`) uniqueness.
- [x] Implement goals CRUD.
- [x] Implement tasks CRUD.
- [x] Implement admin user management (create/edit/deactivate/reactivate).
- [x] Implement per-user workflow toggles (`goal_approval_required`, `report_approval_required`, `can_create_goals`).

## Milestone 3: Dashboards
**Goal:** Provide role-based dashboards that surface performance trends, rankings, and approval work.
**Done when:** Staff dashboard shows trend and anonymized leaderboard, admin dashboard shows full leaderboard and comparison chart, dashboard API endpoints support `fetch()` data loading, and approval queue is available for pending items.
- [x] Build staff dashboard (summary cards, trend chart, anonymized leaderboard).
- [x] Build admin dashboard (summary cards, full leaderboard, comparison chart, approval queue).
- [x] Implement dashboard API endpoints for stats, leaderboard, and comparison data.
- [x] Connect dashboard pages to API data loading via `fetch()`.
- [x] Apply frontend design work using `.agents/skills/frontend-design/SKILL.md`.

## Milestone 4: Admin Settings, Export, Notifications & Polish
**Goal:** Complete operational controls and reporting communication features for day-to-day use.
**Done when:** System configuration is manageable, target snapshots are stored on monthly reports, motivational UX language is present, exports support Excel/PDF with period options and role-based scopes, and toast/bell/achievement notifications are functioning.
- [x] Implement system settings management (`SystemConfig`).
- [x] Persist `target_snapshot` on monthly report records.
- [x] Implement export endpoints for staff self-export, admin user export, and team export.
- [x] Implement Excel (`.xlsx`) and PDF export generation with supported period options.
- [x] Implement toast notifications (success/warning/error/info) behavior.
- [x] Implement bell badge notifications (list, unread/read, mark all as read).
- [x] Implement achievement toast triggers for defined milestones.
- [x] Add motivational language/UX elements from the spec.

## Milestone 5: Bilingual & RTL
**Goal:** Deliver complete bilingual experience with proper English/Arabic behavior and layout direction.
**Done when:** All UI text is translation-key based, EN/AR language files are implemented, RTL layout mirroring works, and language toggle plus saved user preference are operational.
- [x] Externalize all UI strings to translation keys.
- [x] Provide EN/AR translation files.
- [x] Implement language toggle and persist `preferred_lang`.
- [x] Set page-level `lang`/`dir` and RTL layout mirroring.
- [x] Keep charts in LTR behavior per spec.

## Milestone 6: Audit, Testing & Deployment
**Goal:** Ensure compliance, reliability, and readiness for pilot rollout.
**Done when:** All data mutations are covered by audit logging, unit/integration/e2e tests aligned with the product spec Verification Plan are in place, deployment configuration includes Gunicorn/Nginx and backups, and pilot readiness checks are completed.
- [ ] Ensure all data mutations are captured in immutable `AuditLog`.
- [ ] Add automated unit/integration/e2e tests aligned with the Verification Plan.
- [ ] Complete manual verification checklist items from the spec.
- [ ] Prepare deployment config (Gunicorn + Nginx, backups, health check, env settings).
- [ ] Complete pilot readiness checklist.
