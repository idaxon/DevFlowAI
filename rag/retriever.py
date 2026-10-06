import logging
from typing import List, Dict, Any
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore

logger = logging.getLogger("devflow.rag")

class RepositoryRetriever:
    """Retrieves relevant code chunks and context based on developer queries and error logs."""

    def __init__(self, repo_id: str):
        self.repo_id = str(repo_id)
        self.vector_store = VectorStore(self.repo_id)
        self.embedding_model = EmbeddingModel()
        # Initialize embedding model vocabulary from stored chunks if present
        if self.vector_store.chunks:
            texts = [f"{c['path']} {c['code']}" for c in self.vector_store.chunks]
            self.embedding_model.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks with similarity score and metadata."""
        if not self.vector_store.chunks:
            return []

        query_vec = self.embedding_model.transform([query])
        raw_results = self.vector_store.search(query_vec, top_k=top_k)

        formatted_results = []
        for chunk, score in raw_results:
            formatted_results.append({
                "chunk_id": chunk.get("chunk_id"),
                "filename": chunk.get("filename"),
                "path": chunk.get("path"),
                "language": chunk.get("language"),
                "line_start": chunk.get("line_start"),
                "line_end": chunk.get("line_end"),
                "code": chunk.get("code"),
                "similarity_score": round(float(score), 4),
            })

        return formatted_results

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into clean markdown context for agent prompts."""
        if not chunks:
            return "No repository context retrieved."

        lines = ["### RETRIEVED REPOSITORY CONTEXT:"]
        for idx, c in enumerate(chunks, 1):
            lines.append(
                f"\n--- [Snippet {idx}] {c['path']} (Lines {c['line_start']}-{c['line_end']}, Similarity: {c['similarity_score']}) ---\n"
                f"```{c['language']}\n{c['code']}\n```"
            )
        return "\n".join(lines)
