import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import structlog
from prometheus_client import Counter, Gauge, Histogram

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

# Define Prometheus metrics
CAMERA_STATUS = Gauge('camera_status', 'Camera operational status', ['camera_id', 'business_id'])
PERSON_COUNT = Counter('person_detections_total', 'Total number of person detections', ['camera_id', 'zone_id'])
PROCESSING_TIME = Histogram('frame_processing_seconds', 'Time spent processing each frame', ['camera_id'])
DWELL_TIME = Histogram('dwell_time_seconds', 'Customer dwell time in zones', ['zone_id'])
ERROR_COUNT = Counter('processing_errors_total', 'Total number of processing errors', ['camera_id', 'error_type'])

class MonitoringLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Setup loggers
        self.system_logger = structlog.get_logger("system")
        self.analytics_logger = structlog.get_logger("analytics")
        self.error_logger = structlog.get_logger("error")

        # Setup file handlers
        self._setup_file_handlers()

    def _setup_file_handlers(self):
        """Setup file handlers for different log types"""
        # System logs
        system_handler = logging.FileHandler(self.log_dir / "system.log")
        system_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Analytics logs
        analytics_handler = logging.FileHandler(self.log_dir / "analytics.log")
        analytics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

        # Error logs
        error_handler = logging.FileHandler(self.log_dir / "error.log")
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def log_camera_status(self, camera_id: str, business_id: str, status: str, details: Optional[Dict] = None):
        """Log camera operational status"""
        log_data = {
            "camera_id": camera_id,
            "business_id": business_id,
            "status": status,
            "details": details or {}
        }
        self.system_logger.info("camera_status", **log_data)

        # Update Prometheus metric
        CAMERA_STATUS.labels(camera_id=camera_id, business_id=business_id).set(1 if status == "active" else 0)

    def log_analytics(self, camera_id: str, zone_id: str, analytics_data: Dict[str, Any]):
        """Log analytics data"""
        log_data = {
            "camera_id": camera_id,
            "zone_id": zone_id,
            "timestamp": datetime.now().isoformat(),
            "data": analytics_data
        }
        self.analytics_logger.info("analytics_update", **log_data)

        # Update Prometheus metrics
        if 'person_count' in analytics_data:
            PERSON_COUNT.labels(camera_id=camera_id, zone_id=zone_id).inc(analytics_data['person_count'])
        if 'dwell_time' in analytics_data:
            DWELL_TIME.labels(zone_id=zone_id).observe(analytics_data['dwell_time'])

    def log_processing_time(self, camera_id: str, processing_time: float):
        """Log frame processing time"""
        PROCESSING_TIME.labels(camera_id=camera_id).observe(processing_time)

    def log_error(self, camera_id: str, error_type: str, error_msg: str, stack_trace: Optional[str] = None):
        """Log processing errors"""
        log_data = {
            "camera_id": camera_id,
            "error_type": error_type,
            "error_message": error_msg,
            "stack_trace": stack_trace,
            "timestamp": datetime.now().isoformat()
        }
        self.error_logger.error("processing_error", **log_data)

        # Update Prometheus metric
        ERROR_COUNT.labels(camera_id=camera_id, error_type=error_type).inc()

    def get_error_stats(self, camera_id: Optional[str] = None) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        # Read error log file and analyze
        stats = {
            "total_errors": 0,
            "error_types": {},
            "recent_errors": []
        }

        error_log_path = self.log_dir / "error.log"
        if error_log_path.exists():
            with open(error_log_path, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        if camera_id and log_entry.get("camera_id") != camera_id:
                            continue

                        stats["total_errors"] += 1
                        error_type = log_entry.get("error_type", "unknown")
                        stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1

                        # Keep last 10 errors
                        if len(stats["recent_errors"]) < 10:
                            stats["recent_errors"].append(log_entry)
                    except json.JSONDecodeError:
                        continue

        return stats

    def cleanup_old_logs(self, days: int = 30):
        """Clean up logs older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()

monitor = MonitoringLogger()