"""
Metrics and Observability Service
SPEC-AI-FACIL-001 Phase 3: Production monitoring and observability
Tracks performance metrics, error rates, and system health
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LatencyMetric:
    """Latency measurement with percentiles"""
    timestamp: float
    p50: float
    p95: float
    p99: float
    count: int
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsCollector:
    """Collects and aggregates metrics"""

    def __init__(self, retention_seconds: int = 3600):
        """Initialize metrics collector"""
        self.retention_seconds = retention_seconds
        self.start_time = time.time()

        # Metrics storage
        self.counter_metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.gauge_metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.histogram_metrics: Dict[str, List[float]] = defaultdict(list)

        # Aggregated metrics
        self.llm_call_count = 0
        self.llm_success_count = 0
        self.llm_failure_count = 0
        self.llm_latencies: List[float] = []

        self.docs_comment_count = 0
        self.docs_success_count = 0
        self.docs_failure_count = 0
        self.docs_latencies: List[float] = []

        self.approval_count = 0
        self.approval_by_mode: Dict[str, int] = defaultdict(int)

        logger.info("Initialized MetricsCollector")

    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record counter metric"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        self.counter_metrics[name].append(point)
        self._cleanup_old_metrics(name)

    def record_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record gauge metric"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        self.gauge_metrics[name].append(point)
        self._cleanup_old_metrics(name)

    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record histogram value"""
        self.histogram_metrics[name].append(value)

    def record_llm_call(
        self,
        latency_ms: float,
        success: bool,
        mode: str = "default",
        error: Optional[str] = None
    ) -> None:
        """Record LLM API call metric"""
        self.llm_call_count += 1
        self.llm_latencies.append(latency_ms)

        if success:
            self.llm_success_count += 1
            self.record_counter(
                "llm_calls_success",
                tags={"mode": mode}
            )
        else:
            self.llm_failure_count += 1
            self.record_counter(
                "llm_calls_failure",
                tags={"mode": mode, "error": error or "unknown"}
            )

        self.record_histogram("llm_latency_ms", latency_ms, tags={"mode": mode})

    def record_docs_comment(
        self,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Record Google Docs comment posting metric"""
        self.docs_comment_count += 1
        self.docs_latencies.append(latency_ms)

        if success:
            self.docs_success_count += 1
            self.record_counter("docs_comments_success")
        else:
            self.docs_failure_count += 1
            self.record_counter(
                "docs_comments_failure",
                tags={"error": error or "unknown"}
            )

        self.record_histogram("docs_latency_ms", latency_ms)

    def record_approval(
        self,
        decision: str,
        mode: str = "default",
        confidence: float = 0.8
    ) -> None:
        """Record approval decision metric"""
        self.approval_count += 1
        self.approval_by_mode[mode] += 1

        self.record_counter(
            "approvals",
            tags={"decision": decision, "mode": mode}
        )
        self.record_gauge(
            "approval_confidence",
            confidence,
            tags={"mode": mode}
        )

    def get_llm_metrics(self) -> Dict[str, Any]:
        """Get LLM performance metrics"""
        if not self.llm_latencies:
            return {
                "call_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }

        sorted_latencies = sorted(self.llm_latencies)
        n = len(sorted_latencies)

        return {
            "call_count": self.llm_call_count,
            "success_count": self.llm_success_count,
            "failure_count": self.llm_failure_count,
            "success_rate": (self.llm_success_count / self.llm_call_count * 100
                           if self.llm_call_count > 0 else 0),
            "p50": sorted_latencies[int(n * 0.50)] if n > 0 else 0,
            "p95": sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0] if n > 0 else 0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0] if n > 0 else 0,
            "avg": sum(self.llm_latencies) / n if n > 0 else 0
        }

    def get_docs_metrics(self) -> Dict[str, Any]:
        """Get Google Docs performance metrics"""
        if not self.docs_latencies:
            return {
                "comment_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "p50": 0,
                "p95": 0,
                "p99": 0
            }

        sorted_latencies = sorted(self.docs_latencies)
        n = len(sorted_latencies)

        return {
            "comment_count": self.docs_comment_count,
            "success_count": self.docs_success_count,
            "failure_count": self.docs_failure_count,
            "success_rate": (self.docs_success_count / self.docs_comment_count * 100
                           if self.docs_comment_count > 0 else 0),
            "p50": sorted_latencies[int(n * 0.50)] if n > 0 else 0,
            "p95": sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0] if n > 0 else 0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0] if n > 0 else 0,
            "avg": sum(self.docs_latencies) / n if n > 0 else 0
        }

    def get_approval_metrics(self) -> Dict[str, Any]:
        """Get approval decision metrics"""
        return {
            "total_approvals": self.approval_count,
            "by_mode": dict(self.approval_by_mode),
            "approval_rate": (self.approval_count / (self.approval_count or 1)) * 100
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        llm_metrics = self.get_llm_metrics()
        docs_metrics = self.get_docs_metrics()

        llm_healthy = llm_metrics.get("success_rate", 0) > 80
        docs_healthy = docs_metrics.get("success_rate", 0) > 98

        uptime_seconds = time.time() - self.start_time

        return {
            "status": "healthy" if (llm_healthy and docs_healthy) else "degraded",
            "uptime_seconds": uptime_seconds,
            "llm_service": "healthy" if llm_healthy else "degraded",
            "docs_service": "healthy" if docs_healthy else "degraded",
            "llm_success_rate": llm_metrics.get("success_rate", 0),
            "docs_success_rate": docs_metrics.get("success_rate", 0)
        }

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "llm": self.get_llm_metrics(),
            "docs": self.get_docs_metrics(),
            "approvals": self.get_approval_metrics(),
            "health": self.get_health_status()
        }

    def _cleanup_old_metrics(self, name: str) -> None:
        """Remove metrics older than retention period"""
        cutoff_time = time.time() - self.retention_seconds

        if name in self.counter_metrics:
            self.counter_metrics[name] = [
                m for m in self.counter_metrics[name]
                if m.timestamp > cutoff_time
            ]

        if name in self.gauge_metrics:
            self.gauge_metrics[name] = [
                m for m in self.gauge_metrics[name]
                if m.timestamp > cutoff_time
            ]

    def reset(self) -> None:
        """Reset all metrics"""
        self.counter_metrics.clear()
        self.gauge_metrics.clear()
        self.histogram_metrics.clear()
        self.llm_call_count = 0
        self.llm_success_count = 0
        self.llm_failure_count = 0
        self.llm_latencies.clear()
        self.docs_comment_count = 0
        self.docs_success_count = 0
        self.docs_failure_count = 0
        self.docs_latencies.clear()
        self.approval_count = 0
        self.approval_by_mode.clear()
        self.start_time = time.time()
        logger.info("Reset all metrics")


# Global metrics instance
_metrics_instance: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
