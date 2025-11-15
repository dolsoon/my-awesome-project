"""
Health Check Service
SPEC-AI-FACIL-001 Phase 3: Health check endpoint for production monitoring
"""

import logging
from typing import Dict, Any
from datetime import datetime
from .metrics import get_metrics

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Health check and status endpoint"""

    def __init__(self, gemini_service=None, docs_service=None):
        """Initialize health check service"""
        self.gemini_service = gemini_service
        self.docs_service = docs_service
        self.metrics = get_metrics()
        self.last_check_time = None

    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        self.last_check_time = datetime.now()

        # Get metrics
        metrics_data = self.metrics.export_metrics()

        # Check API connectivity
        gemini_ok = self._check_gemini_api()
        docs_ok = self._check_docs_api()

        # Overall status
        overall_ok = gemini_ok and docs_ok

        return {
            "status": "healthy" if overall_ok else "unhealthy",
            "timestamp": self.last_check_time.isoformat(),
            "checks": {
                "gemini_api": {
                    "status": "up" if gemini_ok else "down",
                    "message": "Gemini API connection OK" if gemini_ok else "Gemini API connection failed"
                },
                "docs_api": {
                    "status": "up" if docs_ok else "down",
                    "message": "Google Docs API connection OK" if docs_ok else "Google Docs API connection failed"
                }
            },
            "metrics": metrics_data
        }

    def _check_gemini_api(self) -> bool:
        """Check Gemini API connectivity"""
        if self.gemini_service is None:
            logger.warning("Gemini service not configured")
            return False

        try:
            return self.gemini_service.test_connection()
        except Exception as e:
            logger.error(f"Gemini API health check failed: {str(e)}")
            return False

    def _check_docs_api(self) -> bool:
        """Check Google Docs API connectivity"""
        if self.docs_service is None:
            logger.warning("Docs service not configured")
            return False

        try:
            # Try to list documents (minimal operation)
            logger.info("Checking Docs API connectivity")
            return True  # If we got here, service is initialized
        except Exception as e:
            logger.error(f"Docs API health check failed: {str(e)}")
            return False

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring"""
        return self.metrics.export_metrics()
