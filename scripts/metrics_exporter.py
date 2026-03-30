from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os

from mlops_forecasting.telemetry import render_prometheus_metrics


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in {"/metrics", "/"}:
            self.send_response(404)
            self.end_headers()
            return

        payload = render_prometheus_metrics().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        return


if __name__ == "__main__":
    port = int(os.getenv("METRICS_PORT", "9100"))
    host = os.getenv("METRICS_HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), MetricsHandler)
    print(f"metrics exporter listening on {host}:{port}")
    server.serve_forever()
