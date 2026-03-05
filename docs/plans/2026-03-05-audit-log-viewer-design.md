# Audit Log Viewer — Design

## Scope
Admin-only page at `/settings/audit-log` to browse, filter, and inspect the existing `audit_logs` table. Logs are **immutable** — no clear/delete functionality.

## Architecture
- **Route**: `GET /settings/audit-log` in the existing `settings` blueprint
- **Template**: `settings/audit_log.html` — paginated data table with filters
- **Detail view**: JS modal showing before/after JSON diff on row click

## UI
| Column | Source |
|--------|--------|
| Timestamp | `created_at` formatted |
| Actor | `actor.full_name` |
| Action | `action` (color-coded badge) |
| Entity | `entity_type` + `#entity_id` |
| Target | `target.full_name` (if set) |

### Filters
- Entity type dropdown: all / user / goal / task / monthly_report / system_config
- Action dropdown: all / created / updated / approved / rejected / deactivated / reactivated / password_reset

### Pagination
- 25 entries per page, `?page=N` query param
- Previous/Next links

### Detail Modal
- Click any row → modal shows:
  - Full timestamp, actor, action, entity info
  - **Before** JSON (red) vs **After** JSON (green)
  - Close button

## Files
- `[MODIFY]` `app/settings/routes.py` — add `audit_log()` route
- `[NEW]` `app/templates/settings/audit_log.html` — table + filters + modal
- `[MODIFY]` `app/static/css/style.css` — modal styles + action badges
- `[MODIFY]` `app/templates/base.html` — add sidebar link for Audit Log
- `[MODIFY]` `app/static/js/i18n.js` — add AR translations for new labels
