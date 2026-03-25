"""
Gunicorn configuration file for Alpha Quant Trader Pro API Server
"""

import os

# Server socket
bind = f"{os.getenv('API_SERVER__HOST', '0.0.0.0')}:{os.getenv('API_SERVER__PORT', '8000')}"

# Worker processes
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"  # Changed to ASGI worker for FastAPI
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Restart on code changes (development only)
reload = os.getenv("DEBUG", "false").lower() == "true"