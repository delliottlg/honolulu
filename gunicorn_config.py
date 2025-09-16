import multiprocessing

# Gunicorn configuration file
bind = "0.0.0.0:5007"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

# Logging
accesslog = "/var/log/gunicorn/honolulu_access.log"
errorlog = "/var/log/gunicorn/honolulu_error.log"
loglevel = "info"

# Process naming
proc_name = 'honolulu_hotels'

# Server mechanics
daemon = False
pidfile = '/var/run/honolulu.pid'
user = None
group = None
tmp_upload_dir = None