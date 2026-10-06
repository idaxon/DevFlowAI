import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from rag.chunker import CodeChunker, SUPPORTED_EXTENSIONS
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore

logger = logging.getLogger("devflow.rag")

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
    ".pytest_cache",
    ".idea",
    ".vscode",
    ".mypy_cache",
    "storage",
    "vector_db",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".zip",
    ".tar",
    ".gz",
    ".sqlite",
    ".db",
}

class RepositoryIndexer:
    """Scans and indexes source code repositories into vector databases."""

    def __init__(self, repo_id: str, repo_path: str):
        self.repo_id = str(repo_id)
        self.repo_path = Path(repo_path)
        self.chunker = CodeChunker()
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(self.repo_id)

    def scan_files(self) -> List[Path]:
        """Scan repository directory ignoring non-code and binary paths."""
        valid_files = []
        if not self.repo_path.exists():
            return []

        for root, dirs, files in os.walk(self.repo_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue
                if ext in SUPPORTED_EXTENSIONS or file in SUPPORTED_EXTENSIONS:
                    valid_files.append(Path(root) / file)

        return valid_files

    def index(self) -> Dict[str, Any]:
        """Index the entire repository into the vector store."""
        files = self.scan_files()
        all_chunks = []
        doc_texts = []

        for file_path in files:
            try:
                rel_path = file_path.relative_to(self.repo_path)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                chunks = self.chunker.chunk_file(
                    repo_id=self.repo_id,
                    file_path=str(file_path),
                    relative_path=str(rel_path),
                    content=content,
                )

                for chunk in chunks:
                    all_chunks.append(chunk)
                    doc_texts.append(f"{chunk['path']} {chunk['code']}")
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")

        if not all_chunks:
            return {
                "status": "empty",
                "total_files": 0,
                "total_chunks": 0,
            }

        # Generate embeddings & store
        embeddings = self.embedding_model.fit_transform(doc_texts)
        self.vector_store.add(all_chunks, embeddings)

        return {
            "status": "success",
            "repo_id": self.repo_id,
            "total_files": len(files),
            "total_chunks": len(all_chunks),
            "embedding_dim": embeddings.shape[1] if embeddings.ndim > 1 else 0,
        }
