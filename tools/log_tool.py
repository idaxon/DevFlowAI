import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from database.db import db
from database.models import SystemLog

logger = logging.getLogger("devflow.logs")

class LogTool:
    """System and agent log aggregator."""

    @staticmethod
    def record(workflow_id: Optional[str], source: str, message: str, level: str = "INFO"):
        """Save structured log event to database."""
        try:
            log_entry = SystemLog(
                workflow_id=workflow_id,
                source=source,
                message=message,
                level=level,
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.warning(f"Failed to record log to DB: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

    @staticmethod
    def parse_stack_traces(raw_log: str) -> List[Dict[str, str]]:
        """Extract Python / Node stack traces from raw log streams."""
        traces = []
        pattern = r"Traceback \(most recent call last\):.*?(?=\n\w+Error:|\n\w+Exception:|\Z)(?:.*?\n)?"
        matches = re.findall(pattern, raw_log, re.DOTALL)
        for m in matches:
            traces.append({"trace": m.strip()})
        return traces
