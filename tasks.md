# Project Milestones

## Milestone 1: Foundation
**Goal:** Establish the application foundation with core architecture, data model, authentication, and initial admin access.
**Done when:** The app scaffold, blueprints, extensions, SQLAlchemy models, and migrations are in place; login/register/logout with role decorators works; and an initial admin account can be seeded.

## Milestone 2: Core Features
**Goal:** Deliver the primary operational workflows for report logging, goals/tasks tracking, and admin user control.
**Done when:** Monthly reports, goals, and tasks are manageable via CRUD flows; monthly report uniqueness is enforced; admins can create/edit/deactivate/reactivate users; and per-user workflow toggles are available.

## Milestone 3: Dashboards
**Goal:** Provide role-based dashboards that surface performance trends, rankings, and approval work.
**Done when:** Staff dashboard shows trend and anonymized leaderboard, admin dashboard shows full leaderboard and comparison chart, dashboard API endpoints support `fetch()` data loading, and approval queue is available for pending items.

## Milestone 4: Admin Settings, Export, Notifications & Polish
**Goal:** Complete operational controls and reporting communication features for day-to-day use.
**Done when:** System configuration is manageable, target snapshots are stored on monthly reports, motivational UX language is present, exports support Excel/PDF with period options and role-based scopes, and toast/bell/achievement notifications are functioning.

## Milestone 5: Bilingual & RTL
**Goal:** Deliver complete bilingual experience with proper English/Arabic behavior and layout direction.
**Done when:** All UI text is translation-key based, EN/AR language files are implemented, RTL layout mirroring works, and language toggle plus saved user preference are operational.

## Milestone 6: Audit, Testing & Deployment
**Goal:** Ensure compliance, reliability, and readiness for pilot rollout.
**Done when:** All data mutations are covered by audit logging, unit/integration/e2e tests aligned with the product spec Verification Plan are in place, deployment configuration includes Gunicorn/Nginx and backups, and pilot readiness checks are completed.
