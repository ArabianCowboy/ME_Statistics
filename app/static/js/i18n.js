/**
 * ME Statistics — Internationalization (i18n) Engine
 * =====================================================
 * Hybrid translation: navigation + key headings in Arabic,
 * technical/form labels stay English.
 *
 * Usage: Add `data-i18n="key"` to any element to make it translatable.
 * The toggle updates all elements instantly without page reload.
 */

(function () {
    'use strict';

    // ── Translation Dictionary ───────────────────────────────
    const translations = {
        // Sidebar
        'nav.main': { en: 'Main', ar: 'الرئيسية' },
        'nav.dashboard': { en: 'Dashboard', ar: 'لوحة المعلومات' },
        'nav.reports': { en: 'Monthly Reports', ar: 'التقارير الشهرية' },
        'nav.goals': { en: 'Goals', ar: 'الأهداف' },
        'nav.tasks': { en: 'Tasks', ar: 'المهام' },
        'nav.admin': { en: 'Admin', ar: 'الإدارة' },
        'nav.users': { en: 'Manage Users', ar: 'إدارة المستخدمين' },
        'nav.settings': { en: 'Settings', ar: 'الإعدادات' },
        'app.title': { en: 'ME Statistics', ar: 'إحصائيات ME' },
        'app.subtitle': { en: 'Performance Tracker', ar: 'متتبع الأداء' },

        // Topbar
        'topbar.welcome': { en: 'Welcome back,', ar: 'مرحبًا بعودتك،' },
        'topbar.logout': { en: 'Logout', ar: 'تسجيل خروج' },

        // Bell Dropdown
        'bell.title': { en: 'Notifications', ar: 'الإشعارات' },
        'bell.mark_all': { en: 'Mark all read', ar: 'تعيين الكل كمقروء' },
        'bell.empty': { en: 'No notifications', ar: 'لا توجد إشعارات' },

        // Page Titles
        'page.admin_dashboard': { en: 'Admin Dashboard', ar: 'لوحة معلومات المدير' },
        'page.admin_dashboard_sub': {
            en: 'Team overview, approvals, and performance tracking',
            ar: 'نظرة عامة على الفريق والموافقات وتتبع الأداء'
        },
        'page.staff_dashboard': { en: 'Dashboard', ar: 'لوحة المعلومات' },
        'page.reports': { en: 'Monthly Reports', ar: 'التقارير الشهرية' },
        'page.reports_sub': {
            en: 'Log and track your monthly medication error reports.',
            ar: 'سجّل وتابع تقاريرك الشهرية لأخطاء الأدوية.'
        },
        'page.goals': { en: 'Goals', ar: 'الأهداف' },
        'page.goals_sub': {
            en: 'Set and monitor your professional goals.',
            ar: 'حدّد وتابع أهدافك المهنية.'
        },
        'page.tasks': { en: 'Tasks', ar: 'المهام' },
        'page.tasks_sub': {
            en: 'Break your goals into actionable tasks.',
            ar: 'قسّم أهدافك إلى مهام قابلة للتنفيذ.'
        },
        'page.users': { en: 'Manage Users', ar: 'إدارة المستخدمين' },
        'page.users_sub': {
            en: 'Manage staff accounts, roles, and targets.',
            ar: 'إدارة حسابات الموظفين والأدوار والأهداف.'
        },
        'page.settings': { en: 'System Settings', ar: 'إعدادات النظام' },
        'page.settings_sub': {
            en: 'Configure department settings, targets, and system behavior.',
            ar: 'تكوين إعدادات القسم والأهداف وسلوك النظام.'
        },

        // Dashboard Cards
        'card.active_staff': { en: 'ACTIVE STAFF', ar: 'الموظفون النشطون' },
        'card.pending_approvals': { en: 'PENDING APPROVALS', ar: 'الموافقات المعلقة' },
        'card.team_ytd': { en: 'TEAM YTD TOTAL', ar: 'إجمالي الفريق للسنة' },
        'card.reports_logged': { en: 'reports logged', ar: 'تقرير مسجّل' },
        'card.pending_reg': { en: 'pending registration', ar: 'تسجيل معلّق' },
        'card.reports_ytd': { en: 'REPORTS YTD', ar: 'التقارير للسنة' },
        'card.goals_label': { en: 'GOALS', ar: 'الأهداف' },
        'card.this_month': { en: 'THIS MONTH', ar: 'هذا الشهر' },
        'card.this_month_label': { en: 'Current Month', ar: 'الشهر الحالي' },
        'card.target': { en: 'Target:', ar: 'الهدف:' },
        'card.gap': { en: 'Gap:', ar: 'الفجوة:' },
        'card.goals_in_progress': { en: 'Goals in Progress', ar: 'الأهداف قيد التنفيذ' },
        'card.achievement': { en: "This Month's Achievement", ar: 'إنجاز هذا الشهر' },

        // Leaderboard
        'lb.title': { en: 'Team Leaderboard', ar: 'ترتيب الفريق' },
        'lb.rank': { en: 'RANK', ar: 'الترتيب' },
        'lb.name': { en: 'NAME', ar: 'الاسم' },
        'lb.ytd_total': { en: 'YTD TOTAL', ar: 'إجمالي السنة' },
        'lb.target': { en: 'TARGET', ar: 'الهدف' },
        'lb.achievement': { en: 'ACHIEVEMENT', ar: 'الإنجاز' },

        // Comparison
        'compare.title': { en: 'Staff Comparison', ar: 'مقارنة الموظفين' },
        'compare.btn': { en: 'Compare', ar: 'قارن' },
        'compare.hint': {
            en: 'Select staff members above and click Compare to see the chart.',
            ar: 'اختر الموظفين أعلاه واضغط قارن لعرض الرسم البياني.'
        },

        // Approval Queue
        'approval.title': { en: 'Pending Approvals', ar: 'الموافقات المعلقة' },
        'approval.approve': { en: 'Approve', ar: 'موافقة' },
        'approval.reject': { en: 'Reject', ar: 'رفض' },

        // Trend Chart
        'chart.trend': { en: 'Monthly Trend', ar: 'الاتجاه الشهري' },

        // Encouraging Messages
        'encourage.set_target': { en: 'Set a target to track progress! 📊', ar: 'حدد هدفًا لتتبع التقدم! 📊' },
        'encourage.outstanding': { en: 'Outstanding work! 🌟', ar: 'عمل رائع! 🌟' },
        'encourage.almost': { en: 'Almost there! 🎯', ar: 'أوشكت على الوصول! 🎯' },
        'encourage.got_this': { en: "You've got this! 💪", ar: 'يمكنك فعلها! 💪' },
        'encourage.every_counts': { en: 'Every report counts! 🚀', ar: 'كل تقرير مهم! 🚀' },

        // Actions
        'action.add': { en: 'Add', ar: 'إضافة' },
        'action.export': { en: 'Export Excel', ar: 'تصدير Excel' },
        'action.new_report': { en: 'New Report', ar: 'تقرير جديد' },
        'action.new_goal': { en: 'New Goal', ar: 'هدف جديد' },
        'action.new_task': { en: 'New Task', ar: 'مهمة جديدة' },
        'action.new_user': { en: 'New User', ar: 'مستخدم جديد' },
        'action.create_first_report': { en: 'Create First Report', ar: 'إنشاء أول تقرير' },
        'action.create_first_goal': { en: 'Create First Goal', ar: 'إنشاء أول هدف' },
        'action.create_first_task': { en: 'Create First Task', ar: 'إنشاء أول مهمة' },
        'action.edit': { en: 'Edit', ar: 'تعديل' },
        'action.save': { en: 'Save Settings', ar: 'حفظ الإعدادات' },
        'action.approve': { en: 'Approve', ar: 'موافقة' },
        'action.reject': { en: 'Reject', ar: 'رفض' },

        // Empty States
        'empty.no_reports': { en: 'No Reports Yet', ar: 'لا توجد تقارير بعد' },
        'empty.no_reports_sub': { en: 'Start tracking your monthly ME report submissions.', ar: 'ابدأ بتتبع تقاريرك الشهرية.' },
        'empty.no_goals': { en: 'No Goals Set', ar: 'لا توجد أهداف بعد' },
        'empty.no_goals_sub': { en: 'Set annual goals to track your performance improvement.', ar: 'حدّد أهدافًا سنوية لتتبع تحسن أدائك.' },
        'empty.no_tasks': { en: 'No Tasks Yet', ar: 'لا توجد مهام بعد' },
        'empty.no_tasks_sub': { en: 'Create tasks to track short-term assignments and objectives.', ar: 'أنشئ مهامًا لتتبع المهام والأهداف قصيرة المدى.' },

        // Table Headers
        'th.period': { en: 'Period', ar: 'الفترة' },
        'th.reports': { en: 'Reports', ar: 'التقارير' },
        'th.target': { en: 'Target', ar: 'الهدف' },
        'th.gap': { en: 'Gap', ar: 'الفجوة' },
        'th.achievement': { en: 'Achievement', ar: 'الإنجاز' },
        'th.status': { en: 'Status', ar: 'الحالة' },
        'th.actions': { en: 'Actions', ar: 'الإجراءات' },
        'th.description': { en: 'Description', ar: 'الوصف' },
        'th.priority': { en: 'Priority', ar: 'الأولوية' },
        'th.progress': { en: 'Progress', ar: 'التقدم' },
        'th.created': { en: 'Created', ar: 'تاريخ الإنشاء' },
        'th.user': { en: 'User', ar: 'المستخدم' },
        'th.role': { en: 'Role', ar: 'الدور' },
        'th.joined': { en: 'Joined', ar: 'تاريخ الانضمام' },
        'th.staff': { en: 'Staff', ar: 'الموظف' },
        'th.goal': { en: 'Goal', ar: 'الهدف' },
        'th.submitted': { en: 'Submitted', ar: 'تاريخ التقديم' },
        'th.count': { en: 'Count', ar: 'العدد' },
        'th.rank': { en: 'Rank', ar: 'الترتيب' },
        'th.name': { en: 'Name', ar: 'الاسم' },
        'th.ytd_total': { en: 'YTD Total', ar: 'إجمالي السنة' },

        // Admin Dashboard Cards
        'card.active_staff': { en: 'Active Staff', ar: 'الموظفون النشطون' },
        'card.pending_approvals': { en: 'Pending Approvals', ar: 'الموافقات المعلقة' },
        'card.team_ytd': { en: 'Team YTD Total', ar: 'إجمالي الفريق للسنة' },
        'card.reports_logged': { en: 'reports logged', ar: 'تقرير مسجّل' },
        'card.pending_reg': { en: 'pending registration', ar: 'تسجيل معلّق' },

        // Admin Approval Queue
        'queue.title': { en: 'Approval Queue', ar: 'طابور الموافقات' },
        'queue.pending_goals': { en: 'Pending Goals', ar: 'أهداف معلّقة' },
        'queue.pending_reports': { en: 'Pending Reports', ar: 'تقارير معلّقة' },

        // Settings Sections
        'settings.department': { en: 'Department', ar: 'القسم' },
        'settings.targets': { en: 'Targets & Fiscal Year', ar: 'الأهداف والسنة المالية' },
        'settings.preferences': { en: 'Preferences', ar: 'التفضيلات' },
        'settings.behavior': { en: 'System Behavior', ar: 'سلوك النظام' },
        'settings.self_reg': { en: 'Allow Self-Registration', ar: 'السماح بالتسجيل الذاتي' },
        'settings.self_reg_hint': { en: 'When enabled, new users can register themselves. They still require admin approval.', ar: 'عند التفعيل، يمكن للمستخدمين الجدد التسجيل بأنفسهم. يتطلب موافقة المدير.' },
        'settings.leaderboard': { en: 'Show Leaderboard to Staff', ar: 'عرض الترتيب للموظفين' },
        'settings.leaderboard_hint': { en: 'Anonymized leaderboard visible on staff dashboards.', ar: 'ترتيب مجهول الهوية يظهر في لوحات الموظفين.' },

        // Status Badges
        'status.approved': { en: 'Approved', ar: 'تمت الموافقة' },
        'status.pending': { en: 'Pending', ar: 'قيد الانتظار' },
        'status.active': { en: 'Active', ar: 'نشط' },
        'status.inactive': { en: 'Inactive', ar: 'غير نشط' },
        'status.pending_approval': { en: 'Pending Approval', ar: 'بانتظار الموافقة' },
        'status.rejected': { en: 'Rejected', ar: 'مرفوض' },

        // Users Page
        'users.subtitle': { en: 'Create, edit, and manage user accounts.', ar: 'إنشاء وتعديل وإدارة حسابات المستخدمين.' },
        'users.pending': { en: 'pending approval', ar: 'بانتظار الموافقة' },

        // Audit Log
        'nav.audit_log': { en: 'Audit Log', ar: 'سجل المراجعة' },
        'page.audit_log': { en: 'Audit Log', ar: 'سجل المراجعة' },
        'audit.subtitle': { en: 'Browse system activity and changes.', ar: 'تصفح نشاط النظام والتغييرات.' },
        'audit.entity_type': { en: 'Entity Type', ar: 'نوع الكيان' },
        'audit.action': { en: 'Action', ar: 'الإجراء' },
        'audit.all': { en: 'All', ar: 'الكل' },
        'audit.clear_filters': { en: 'Clear Filters', ar: 'مسح الفلاتر' },
        'audit.th_time': { en: 'Timestamp', ar: 'الوقت' },
        'audit.th_actor': { en: 'Actor', ar: 'المنفذ' },
        'audit.th_action': { en: 'Action', ar: 'الإجراء' },
        'audit.th_entity': { en: 'Entity', ar: 'الكيان' },
        'audit.th_target': { en: 'Target', ar: 'الهدف' },
        'audit.th_details': { en: 'Details', ar: 'التفاصيل' },
        'audit.empty': { en: 'No Audit Entries', ar: 'لا توجد سجلات' },
        'audit.empty_sub': { en: 'Activity will appear here as users interact with the system.', ar: 'سيظهر النشاط هنا عندما يتفاعل المستخدمون مع النظام.' },
        'audit.detail_title': { en: 'Change Details', ar: 'تفاصيل التغيير' },
    };

    // ── State ────────────────────────────────────────────────
    let currentLang = localStorage.getItem('lang') || 'en';

    // ── Core Functions ───────────────────────────────────────

    function t(key) {
        const entry = translations[key];
        if (!entry) return key;
        return entry[currentLang] || entry.en || key;
    }

    function applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            const key = el.getAttribute('data-i18n');
            const translated = t(key);
            // For inputs, set placeholder; for others, set text
            if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
                el.placeholder = translated;
            } else {
                el.textContent = translated;
            }
        });
    }

    function setDirection() {
        const html = document.documentElement;
        if (currentLang === 'ar') {
            html.setAttribute('dir', 'rtl');
            html.setAttribute('lang', 'ar');
        } else {
            html.setAttribute('dir', 'ltr');
            html.setAttribute('lang', 'en');
        }
    }

    function updateToggleButtons() {
        const enBtn = document.getElementById('lang-en');
        const arBtn = document.getElementById('lang-ar');
        if (enBtn && arBtn) {
            enBtn.classList.toggle('topbar__lang-btn--active', currentLang === 'en');
            arBtn.classList.toggle('topbar__lang-btn--active', currentLang === 'ar');
        }
    }

    function switchLang(lang) {
        currentLang = lang;
        localStorage.setItem('lang', lang);
        setDirection();
        applyTranslations();
        updateToggleButtons();
    }

    // ── Initialize ───────────────────────────────────────────
    // Apply immediately (before DOMContentLoaded if possible)
    setDirection();

    document.addEventListener('DOMContentLoaded', function () {
        applyTranslations();
        updateToggleButtons();

        // Wire toggle buttons
        var enBtn = document.getElementById('lang-en');
        var arBtn = document.getElementById('lang-ar');

        if (enBtn) {
            enBtn.addEventListener('click', function () { switchLang('en'); });
        }
        if (arBtn) {
            arBtn.addEventListener('click', function () { switchLang('ar'); });
        }
    });

    // Expose for external use
    window.i18n = { t: t, switchLang: switchLang, currentLang: function () { return currentLang; } };
})();
