import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger("devflow.services.validation")

class ValidationService:
    """Multi-stage verification engine checking syntax, tests, and deployment health."""

    @staticmethod
    def validate_code_safety(code_str: str) -> Dict[str, Any]:
        """Perform security static checks on generated code."""
        dangerous_tokens = ["os.system(", "eval(", "exec(", "shutil.rmtree('/'", "DROP TABLE"]
        found_threats = [t for t in dangerous_tokens if t in code_str]

        return {
            "safe": len(found_threats) == 0,
            "threats_detected": found_threats,
        }
