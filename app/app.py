import os
import sys
import time
import signal
import logging
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("telemetry")

STU_ID = os.getenv("STU_ID", "230252")
STU_VARIANT = os.getenv("STU_VARIANT", "36")
PORT = int(os.getenv("PORT", 8116))
ALERT_THRESHOLD_C = os.getenv("ALERT_THRESHOLD_C", "unknown")
DB_PASSWORD = os.getenv("DB_PASSWORD", None)

logger.info(f"Starting telemetry with STU_ID={STU_ID}, STU_VARIANT={STU_VARIANT}, PORT={PORT}")
logger.info(f"ConfigMap ALERT_THRESHOLD_C={ALERT_THRESHOLD_C}")
if DB_PASSWORD:
    logger.info("Secret DB_PASSWORD is set (not printed)")
else:
    logger.warning("Secret DB_PASSWORD is NOT set")

START = time.time()
WARMUP = 5

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health/live":
            code, body = 200, '{"status":"alive"}'
        elif self.path == "/health/ready":
            if time.time() - START >= WARMUP:
                code, body = 200, '{"status":"ready"}'
            else:
                code, body = 503, '{"status":"warming up"}'
        else:
            code, body = 200, f'{{"pod":"{socket.gethostname()}","version":"1.0.0"}}'
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

def graceful_shutdown(signum, frame):
    logger.info("Graceful shutdown initiated...")
    logger.info("Graceful shutdown complete.")
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    logger.info(f"Server listening on port {PORT}")
    server.serve_forever()
    