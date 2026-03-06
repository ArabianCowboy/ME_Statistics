# Backup & Restore System — Design

## Scope
Admin-only backup management page at `/settings/backups`. Manual/auto SQLite backup, configurable schedule, per-backup restore with type-to-confirm safety, auto-retention.

## Architecture
- **Backend**: `shutil.copy2()` for backup, file replacement for restore
- **Storage**: `instance/backups/` directory
- **Config**: `SystemConfig` keys for interval + retention
- **Auto-backup**: checked on admin settings page load via `before_request` hook
- **Pre-restore safety**: auto-backup before any restore operation

## UI Layout
Two top cards (Status + Config) + backup list table + restore confirmation modal.

### Status Card
- Health indicator (green/amber/red based on backup age vs interval)
- Last backup time, count, total size
- "Backup Now" button

### Config Card
- Toggle: Enable Auto-Backup
- Dropdown: Interval (1/3/7/14/30 days)
- Dropdown: Keep latest (5/10/20/50 backups)
- Save button

### Backup List Table
- Columns: Date/Time, Size, Actions (Restore, Delete)
- Each row has its own Restore button → type "RESTORE" to confirm

### Restore Modal
- Warning message explaining the operation
- Text input requiring exact "RESTORE" to enable confirm button
- Auto-creates pre-restore backup first

## Files
- `[MODIFY]` `app/settings/routes.py` — backup/restore/delete/config routes
- `[NEW]` `app/templates/settings/backups.html` — full page template
- `[MODIFY]` `app/static/css/style.css` — backup page styles
- `[MODIFY]` `app/templates/base.html` — sidebar link
- `[MODIFY]` `app/static/js/i18n.js` — Arabic translations
