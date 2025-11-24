"""
Monitoring Service
Tracks application metrics and health
"""
import os
import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Application monitoring service
    Tracks system metrics, errors, and performance
    """

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.slow_request_count = 0

    def record_request(self):
        """Record an API request"""
        self.request_count += 1

    def record_error(self):
        """Record an error"""
        self.error_count += 1

    def record_slow_request(self):
        """Record a slow request (> 1s)"""
        self.slow_request_count += 1

    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_percent": disk.percent
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        uptime = self.get_uptime()
        uptime_hours = uptime / 3600

        # Calculate error rate
        error_rate = 0
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100

        # Determine health status
        status = "healthy"
        if error_rate > 5:
            status = "degraded"
        elif error_rate > 10:
            status = "unhealthy"

        return {
            "status": status,
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime_hours, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate_percent": round(error_rate, 2),
                "slow_requests": self.slow_request_count
            }
        }

    def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health check including system metrics"""
        health = self.get_health_status()
        system_metrics = self.get_system_metrics()

        return {
            **health,
            "system": system_metrics,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0"
        }


# Global monitoring instance
monitoring_service = MonitoringService()


# Example usage
if __name__ == "__main__":
    service = MonitoringService()

    # Simulate some requests
    for _ in range(100):
        service.record_request()

    service.record_error()
    service.record_slow_request()

    print("Health Status:")
    print(service.get_health_status())

    print("\nDetailed Health:")
    print(service.get_detailed_health())
