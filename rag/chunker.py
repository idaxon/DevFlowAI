import os
import uuid
from typing import List, Dict, Any

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "bash",
    ".env.example": "config",
    "Dockerfile": "dockerfile",
    "requirements.txt": "requirements",
    "package.json": "json",
}

class CodeChunker:
    """Splits source code and configurations into contextual chunks with rich metadata."""

    def __init__(self, chunk_size_lines: int = 35, overlap_lines: int = 10):
        self.chunk_size_lines = chunk_size_lines
        self.overlap_lines = overlap_lines

    def chunk_file(self, repo_id: str, file_path: str, relative_path: str, content: str) -> List[Dict[str, Any]]:
        """Chunk a single file into overlapping line windows with metadata."""
        ext = os.path.splitext(file_path)[1]
        basename = os.path.basename(file_path)
        language = SUPPORTED_EXTENSIONS.get(ext, SUPPORTED_EXTENSIONS.get(basename, "text"))

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        # If file is small, make it a single chunk
        if total_lines <= self.chunk_size_lines:
            return [{
                "chunk_id": f"{repo_id}_{str(uuid.uuid4())[:8]}",
                "repository": repo_id,
                "filename": basename,
                "path": relative_path.replace("\\", "/"),
                "language": language,
                "line_start": 1,
                "line_end": total_lines,
                "code": content,
                "total_lines": total_lines,
            }]

        chunks = []
        step = max(1, self.chunk_size_lines - self.overlap_lines)
        for i in range(0, total_lines, step):
            start_line = i
            end_line = min(i + self.chunk_size_lines, total_lines)
            chunk_lines = lines[start_line:end_line]
            chunk_text = "\n".join(chunk_lines)

            chunks.append({
                "chunk_id": f"{repo_id}_{str(uuid.uuid4())[:8]}",
                "repository": repo_id,
                "filename": basename,
                "path": relative_path.replace("\\", "/"),
                "language": language,
                "line_start": start_line + 1,
                "line_end": end_line,
                "code": chunk_text,
                "total_lines": total_lines,
            })

            if end_line >= total_lines:
                break

        return chunks
