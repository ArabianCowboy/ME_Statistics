# ME Statistics — Gunicorn Production Config
# =============================================
# Usage: gunicorn -c gunicorn.conf.py "app:create_app('production')"

import multiprocessing

# ── Server Socket ────────────────────────────────────────────
bind = "127.0.0.1:8000"
backlog = 2048

# ── Worker Processes ─────────────────────────────────────────
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 4
worker_connections = 1000
timeout = 120
keepalive = 5

# ── Logging ──────────────────────────────────────────────────
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ── Process Naming ───────────────────────────────────────────
proc_name = "me_statistics"

# ── Security ─────────────────────────────────────────────────
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# ── Pre-fork Hook ────────────────────────────────────────────
def on_starting(server):
    """Ensure logs directory exists."""
    import os
    os.makedirs("logs", exist_ok=True)
