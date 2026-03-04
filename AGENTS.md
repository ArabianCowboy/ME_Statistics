# AGENTS.md

This file guides coding agents working in this repository.
Follow it unless a direct user instruction overrides it.

## 1) Repository State
- Current tracked files are mostly planning docs plus one example spreadsheet.
- There is no committed Flask scaffold in the current working tree yet.
- Treat this repo as design-first now, implementation-next.
- Implementation intent lives in:
  - `docs/plans/product-spec.md`
  - `docs/plans/roadmap.md`

## 2) Expected Stack and Shape
- Backend: Python 3.9+ with Flask.
- ORM/migrations: SQLAlchemy + Flask-Migrate.
- Database: SQLite (WAL mode planned).
- Auth/forms: Flask-Login + Flask-WTF/WTForms.
- Templating: Jinja2 server-rendered pages.
- Frontend: vanilla CSS/JS with Chart.js.
- i18n: English/Arabic with RTL/LTR support.
- Export: openpyxl (`.xlsx`) and ReportLab (`.pdf`).
- Architecture: modular monolith with blueprints (`auth`, `dashboard`, `logs`, `users`, `export`).

## 3) Setup, Build, and Run Commands
Use these once the roadmap scaffold files exist.

### Environment setup
- `python -m venv .venv`
- Linux/macOS activate: `source .venv/bin/activate`
- Windows PowerShell activate: `.venv\\Scripts\\Activate.ps1`
- `pip install -r requirements.txt`

### App run
- Planned baseline: `python run.py`
- Flask CLI alternative: `flask --app run.py run --debug`
- Production style (if configured): `gunicorn "run:app"`

### Database and migrations
- Init migrations (first time): `flask --app run.py db init`
- New migration: `flask --app run.py db migrate -m "message"`
- Upgrade DB: `flask --app run.py db upgrade`
- Downgrade one step (careful): `flask --app run.py db downgrade`

## 4) Lint, Format, and Type Check
No lint/format/type config is committed yet; use these defaults.

- Lint: `ruff check .`
- Lint auto-fix: `ruff check . --fix`
- Format: `ruff format .`
- Type check (when configured): `mypy app tests`

## 5) Test Commands (including single test)
Preferred runner: `pytest`.

- All tests: `pytest`
- Quiet mode: `pytest -q`
- Stop on first failure: `pytest -x`
- Unit only: `pytest tests/unit -q`
- Integration only: `pytest tests/integration -q`
- E2E only: `pytest tests/e2e -q`

Single-test patterns:
- Single file: `pytest tests/unit/test_auth.py -q`
- Single function: `pytest tests/unit/test_auth.py::test_login_success -q`
- Single class: `pytest tests/unit/test_auth.py::TestLogin -q`
- Keyword filter: `pytest -k "login and not slow" -q`
- Last failed: `pytest --lf`

## 6) File Placement and Architecture Rules
- Put application code under `app/`.
- Keep features in blueprints, not one giant routes file.
- Keep extension instances in `app/extensions.py`.
- Keep core models in `app/models.py` unless a split is justified.
- Keep route handlers thin; move computation to service modules.
- Put forms in each blueprint `forms.py`.
- Put export builders in `app/export/generators.py`.
- Keep templates in `app/templates/` and assets in `app/static/`.
- Keep tests in `tests/unit`, `tests/integration`, `tests/e2e`.

## 7) Python Style Guidelines
- Follow PEP 8 and target ~88-char lines.
- Prefer explicit, readable code over compact clever code.
- Use absolute imports from `app`; avoid deep relative imports.
- Import order: stdlib, third-party, local.
- Separate import groups with one blank line.
- Never use wildcard imports.
- Prefer f-strings.
- Keep functions small and single-purpose.
- Add docstrings to every new/edited module, class, and function.
- Docstrings should cover purpose, inputs, return value, side effects, and raised errors.
- Add inline comments for non-obvious business rules, formulas, and edge cases.
- Comments should explain *why*; avoid repeating what code already states.

## 8) Types and Data Contracts
- Add type hints to all new/edited Python functions.
- Keep Python 3.9 compatibility (`Optional[T]`, `List[T]`, `Dict[K, V]`).
- Use precise return types in services/utilities.
- Use enums/constants for bounded domain values (`role`, `status`, `priority`).
- Keep boundary contracts explicit (forms, API JSON, exports).

## 9) Naming Conventions
- Files/modules: `snake_case.py`
- Functions/variables: `snake_case`
- Classes/forms/models: `PascalCase`
- Constants/env keys: `UPPER_SNAKE_CASE`
- Boolean names should read naturally (`is_active`, `is_approved`, `can_create_goals`).
- Template names should be feature-specific (`reports.html`, `settings.html`).

## 10) Flask, Routes, and Forms
- Use the app factory pattern in `app/__init__.py`.
- Keep endpoint names descriptive and stable.
- Enforce auth/role checks server-side on all protected routes.
- Validate all POST payloads with WTForms before mutating state.
- Use Post/Redirect/Get after successful form submissions.
- Return JSON only from explicit API endpoints.

## 11) Error Handling and Logging
- Fail fast on invalid input with clear user-safe messages.
- Catch specific exceptions; avoid broad `except Exception`.
- On DB write failure: rollback, log context, return safe message.
- Use proper HTTP errors (`abort(403)`, `abort(404)`, etc.) for violations.
- Never leak stack traces, secrets, or internal SQL details to users.
- Record all data mutations in immutable audit logs.

## 12) Security and Privacy Baseline
- Hash passwords properly; never store plaintext.
- Keep CSRF protection on for all state-changing forms.
- Use secure session cookie settings in production.
- Enforce least privilege for staff/admin boundaries.
- Keep secrets in environment variables, never in git.
- Never commit `.env`, DB files, backups, or generated credentials.

## 13) Frontend and i18n Rules
- Preserve the documented warm, motivational design direction.
- Follow design tokens and palette from the design document.
- Prefer native CSS for V1; do not introduce Tailwind unless explicitly requested.
- Avoid inline styles except for truly dynamic runtime values.
- Keep JS lightweight; avoid unnecessary frameworks.
- Maintain responsive behavior for desktop/tablet/mobile.
- Keep all user-visible strings translatable.
- Support RTL layout in Arabic mode while keeping charts readable.

## 14) Testing Expectations per Change
- Add or update tests for every behavior change.
- For bug fixes, add a regression test that fails before the fix.
- Prefer unit tests for pure logic and calculations.
- Use integration tests for route+db+auth workflows.
- Use e2e tests for key journeys (register, approve, log, export).
- Keep fixtures/data deterministic and minimal.

## 15) Agent Workflow and Done Criteria
- Read relevant sections in `docs/plans/` before implementation.
- Make the smallest safe change that solves the requested task.
- Run the narrowest useful lint/format/test commands before finishing.
- If blocked by missing tooling, report exactly what is missing.
- Update docs when behavior, commands, or architecture assumptions change.
- Finish only when security/validation are in place, tests pass (or blockers are explicit), and no secrets/local artifacts are committed.
