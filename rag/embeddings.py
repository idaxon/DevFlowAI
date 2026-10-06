import os
import logging
import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from config import Config

logger = logging.getLogger("devflow.rag")

class EmbeddingModel:
    """Computes vector representations of source code and queries."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[\w\.\-\_\/]+\b",
            max_features=5000,
            lowercase=True
        )
        self.is_fitted = False

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Fit vectorizer on repo documents and return normalized matrix."""
        if not texts:
            return np.zeros((0, 10), dtype=np.float32)
        matrix = self.vectorizer.fit_transform(texts).toarray()
        # L2 normalize rows
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.is_fitted = True
        return (matrix / norms).astype(np.float32)

    def transform(self, texts: List[str]) -> np.ndarray:
        """Transform queries or new chunks into normalized vectors."""
        if not self.is_fitted or not texts:
            return np.zeros((len(texts), 1), dtype=np.float32)
        try:
            matrix = self.vectorizer.transform(texts).toarray()
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return (matrix / norms).astype(np.float32)
        except Exception as e:
            logger.warning(f"Vector transformation fallback: {e}")
            return np.zeros((len(texts), self.vectorizer.max_features or 100), dtype=np.float32)
