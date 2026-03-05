/**
 * ME Statistics — Toast Notification System
 * ============================================
 * Vanilla JS toast: slides in from right, auto-dismisses after 4s,
 * max 3 visible, click ✕ to dismiss early.
 */

(function () {
    'use strict';

    const TOAST_DURATION = 4000;
    const MAX_VISIBLE = 3;

    // Icons for each toast type (inline SVG)
    const ICONS = {
        success: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    // Create container
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    /**
     * Show a toast notification.
     * @param {string} message  - Toast message text
     * @param {string} type     - 'success' | 'error' | 'warning' | 'info'
     */
    window.showToast = function (message, type) {
        type = type || 'info';

        // Enforce max visible
        const existing = container.querySelectorAll('.toast');
        if (existing.length >= MAX_VISIBLE) {
            dismissToast(existing[0]);
        }

        const toast = document.createElement('div');
        toast.className = 'toast toast--' + type;
        toast.innerHTML =
            '<div class="toast__icon">' + (ICONS[type] || ICONS.info) + '</div>' +
            '<div class="toast__message">' + escapeHtml(message) + '</div>' +
            '<button class="toast__close" aria-label="Dismiss">&times;</button>' +
            '<div class="toast__progress"><div class="toast__progress-bar"></div></div>';

        container.appendChild(toast);

        // Trigger enter animation
        requestAnimationFrame(function () {
            toast.classList.add('toast--visible');
        });

        // Close button
        toast.querySelector('.toast__close').addEventListener('click', function () {
            dismissToast(toast);
        });

        // Auto-dismiss
        const timer = setTimeout(function () {
            dismissToast(toast);
        }, TOAST_DURATION);

        toast._timer = timer;
    };

    function dismissToast(toast) {
        if (toast._dismissed) return;
        toast._dismissed = true;
        clearTimeout(toast._timer);
        toast.classList.remove('toast--visible');
        toast.classList.add('toast--exit');
        setTimeout(function () {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();
