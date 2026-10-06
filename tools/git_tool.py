import os
import shutil
import difflib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import Config

logger = logging.getLogger("devflow.tools")

class GitTool:
    """Manages isolated workspaces, branches, patches, and unified diffs."""

    def __init__(self, workspace_base: Optional[Path] = None):
        self.workspace_base = workspace_base or Config.WORKSPACE_DIR
        self.workspace_base.mkdir(parents=True, exist_ok=True)

    def create_isolated_workspace(self, workflow_id: str, source_repo_path: str) -> Path:
        """Create an isolated sandbox workspace for the workflow."""
        workflow_workspace = self.workspace_base / str(workflow_id)
        if workflow_workspace.exists():
            shutil.rmtree(workflow_workspace, ignore_errors=True)
        
        # Copy source files to workspace ignoring .git / caches / recursive repo storage / databases
        shutil.copytree(
            source_repo_path,
            workflow_workspace,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", 
                "venv", ".venv", "env", "node_modules", 
                "repositories", "vector_db", "instance", ".gemini", "scratch",
                "*.db", "*.sqlite", "*.sqlite3", "devflow.db*", "*.log", "reports", "storage"
            )
        )
        return workflow_workspace

    def apply_file_modification(self, workspace_path: Path, relative_file_path: str, new_content: str) -> Dict[str, Any]:
        """Safely write modified code to the isolated workspace."""
        target_file = workspace_path / relative_file_path
        target_file.parent.mkdir(parents=True, exist_ok=True)

        original_content = ""
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "file": relative_file_path,
            "bytes_written": len(new_content),
            "had_original": bool(original_content),
        }

    def generate_diff(self, original_path: Path, workspace_path: Path) -> str:
        """Generate a complete unified diff between original repo and workspace for text source code files only."""
        diff_lines = []
        binary_extensions = {
            ".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".pyd", ".png", ".jpg", 
            ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip", ".tar", ".gz", ".7z",
            ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".pkl", ".parquet"
        }

        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "node_modules", "repositories", "vector_db")]
            for file in files:
                # Skip binary extensions and database files
                if any(file.endswith(ext) for ext in binary_extensions) or file.startswith("devflow.db"):
                    continue

                ws_file = Path(root) / file
                rel_path = ws_file.relative_to(workspace_path)
                orig_file = original_path / rel_path

                if orig_file.exists():
                    try:
                        # Check for binary null bytes
                        with open(orig_file, "rb") as f:
                            orig_bytes = f.read(8192)
                        with open(ws_file, "rb") as f:
                            ws_bytes = f.read(8192)
                        if b'\x00' in orig_bytes or b'\x00' in ws_bytes:
                            continue

                        with open(orig_file, "r", encoding="utf-8", errors="ignore") as f:
                            orig_text = f.readlines()
                        with open(ws_file, "r", encoding="utf-8", errors="ignore") as f:
                            ws_text = f.readlines()

                        file_diff = list(difflib.unified_diff(
                            orig_text,
                            ws_text,
                            fromfile=f"a/{str(rel_path).replace(chr(92), '/')}",
                            tofile=f"b/{str(rel_path).replace(chr(92), '/')}",
                            lineterm="",
                        ))
                        if file_diff:
                            diff_lines.extend(file_diff)
                    except Exception as e:
                        logger.warning(f"Error computing diff for {rel_path}: {e}")
                else:
                    # New file
                    try:
                        with open(ws_file, "rb") as f:
                            ws_bytes = f.read(8192)
                        if b'\x00' in ws_bytes:
                            continue

                        with open(ws_file, "r", encoding="utf-8", errors="ignore") as f:
                            ws_text = f.readlines()
                        file_diff = list(difflib.unified_diff(
                            [],
                            ws_text,
                            fromfile="/dev/null",
                            tofile=f"b/{str(rel_path).replace(chr(92), '/')}",
                            lineterm="",
                        ))
                        if file_diff:
                            diff_lines.extend(file_diff)
                    except Exception:
                        pass

        return "\n".join(diff_lines) if diff_lines else ""
