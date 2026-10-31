"""
Metrics & Execution Tracing for Multi-Agent System.
Persists and calculates real observability metrics:
- Total tasks, success/failure counts
- Execution times per agent and pipeline
- Sources indexed
- Real budget cost (₹0.00 local compute)
"""
import os
import sys
import json
import time
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")

logger = logging.getLogger("multi_agent.utils.metrics")

class MetricsTracker:
    """Manages persistent execution telemetry without third-party cloud services."""
    
    def __init__(self, storage_path: str = METRICS_FILE):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            initial_data = {
                "tasks": [],
                "summary": {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0,
                    "avg_execution_time_seconds": 0.0,
                    "total_sources_collected": 0,
                    "total_cost_inr": 0.00,
                    "total_cost_usd": 0.00
                }
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_metrics(self) -> Dict[str, Any]:
        """Reads persisted metrics."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading metrics: {e}")
            return {"tasks": [], "summary": {}}

    def record_run(
        self,
        topic: str,
        duration_seconds: float,
        success: bool,
        sources_count: int,
        agent_statuses: Dict[str, str],
        error_msg: str = None
    ) -> Dict[str, Any]:
        """
        Records an individual task execution and updates running averages.
        """
        data = self.load_metrics()
        
        task_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": topic,
            "duration_seconds": round(duration_seconds, 2),
            "success": success,
            "sources_collected": sources_count,
            "agent_statuses": agent_statuses,
            "cost_inr": 0.0,
            "cost_usd": 0.0,
            "error": error_msg
        }
        
        data["tasks"].append(task_record)
        
        # Calculate derived metrics from actual history (no invented stats)
        all_tasks = data["tasks"]
        total = len(all_tasks)
        successful = sum(1 for t in all_tasks if t.get("success", False))
        failed = total - successful
        total_time = sum(t.get("duration_seconds", 0.0) for t in all_tasks)
        avg_time = round(total_time / total, 2) if total > 0 else 0.0
        total_sources = sum(t.get("sources_collected", 0) for t in all_tasks)
        
        data["summary"] = {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": failed,
            "avg_execution_time_seconds": avg_time,
            "total_sources_collected": total_sources,
            "total_cost_inr": 0.00,  # 100% Free / Open Source Local Execution
            "total_cost_usd": 0.00
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Persisted metrics for '{topic}' (Elapsed: {duration_seconds:.1f}s, Success: {success})")
        return data["summary"]

# Singleton instance
tracker = MetricsTracker()

