import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config import Config

class VectorStore:
    """Stores chunks and embeddings per repository with disk persistence."""

    def __init__(self, repo_id: str):
        self.repo_id = str(repo_id)
        self.save_dir = Path(Config.VECTOR_DB_DIR) / f"repo_{self.repo_id}"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = np.zeros((0, 1), dtype=np.float32)
        self.load()

    def add(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        """Add chunks and embedding matrix to store and save to disk."""
        self.chunks = chunks
        self.embeddings = embeddings
        self.save()

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Perform cosine similarity top-k search against indexed chunks."""
        if len(self.chunks) == 0 or self.embeddings.shape[0] == 0:
            return []

        # query_vec shape: (1, dim), embeddings shape: (N, dim)
        if query_vec.shape[1] != self.embeddings.shape[1]:
            return []

        scores = np.dot(self.embeddings, query_vec.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append((self.chunks[idx], score))
        return results

    def save(self):
        """Persist vector index and metadata to disk."""
        meta_file = self.save_dir / "chunks.json"
        vec_file = self.save_dir / "vectors.npy"

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

        np.save(vec_file, self.embeddings)

    def load(self):
        """Load vector index and metadata from disk if present."""
        meta_file = self.save_dir / "chunks.json"
        vec_file = self.save_dir / "vectors.npy"

        if meta_file.exists() and vec_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.embeddings = np.load(vec_file)
            except Exception:
                self.chunks = []
                self.embeddings = np.zeros((0, 1), dtype=np.float32)
