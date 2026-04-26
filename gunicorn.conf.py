import multiprocessing
import os

bind = os.environ.get("BIND_ADDRESS", "0.0.0.0:5000")
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
timeout = 120
keepalive = 5

max_requests = 1000
max_requests_jitter = 50

accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

capture_output = True
enable_stdio_inheritance = True

reload = os.environ.get("FLASK_ENV", "development") == "development"