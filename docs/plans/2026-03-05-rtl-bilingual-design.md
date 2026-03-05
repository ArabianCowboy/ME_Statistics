# RTL/Bilingual (Arabic) Support — Design

## Scope
Hybrid translation: navigation labels + key headings in Arabic, technical/form labels stay English. Instant toggle via JS + CSS, no page reload. Persisted in localStorage.

## Architecture
- **CSS**: `[dir="rtl"]` selectors mirror layout (sidebar, margins, text alignment, toasts)
- **JS**: `i18n.js` with EN/AR dictionary + `data-i18n` attributes on translatable elements
- **Persistence**: `localStorage.getItem('lang')` read on page load, applied before render

## Translation Scope
| Arabic | English (stays) |
|--------|----------------|
| Sidebar nav labels | Form field labels |
| Page titles | Table column headers |
| Encouraging messages | Button text |
| Topbar welcome | Toast messages |
| Empty states | Technical terms |

## RTL Layout
- Sidebar: left → right
- Text alignment: right-aligned
- Margins/paddings flip via CSS logical properties
- Toast slides from left
- Charts remain LTR

## Files
- `[NEW]` `app/static/js/i18n.js`
- `[MODIFY]` `base.html` — data-i18n, script, toggle wiring
- `[MODIFY]` `style.css` — `[dir="rtl"]` rules
- `[MODIFY]` All page templates — data-i18n on headings
