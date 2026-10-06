import pytest
import numpy as np
from pathlib import Path
from rag.chunker import CodeChunker
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.indexer import RepositoryIndexer
from rag.retriever import RepositoryRetriever
from config import Config

def test_code_chunker():
    chunker = CodeChunker(chunk_size_lines=10, overlap_lines=2)
    sample_code = "\n".join([f"line_{i} = {i}" for i in range(25)])
    chunks = chunker.chunk_file("test_repo", "app.py", "app.py", sample_code)
    
    assert len(chunks) >= 3
    assert chunks[0]["filename"] == "app.py"
    assert chunks[0]["line_start"] == 1
    assert "line_0" in chunks[0]["code"]

def test_embeddings_and_vector_store(tmp_path):
    model = EmbeddingModel()
    texts = [
        "def get_users(): return database.query()",
        "DATABASE_URL = os.getenv('DATABASE_URL')",
        "docker build -t app ."
    ]
    matrix = model.fit_transform(texts)
    assert matrix.shape[0] == 3
    assert matrix.shape[1] > 0

    # Query transformation
    q_vec = model.transform(["database connection error"])
    assert q_vec.shape[0] == 1

    # Store
    store = VectorStore("test_unit")
    store.add([{"chunk_id": f"c_{i}", "code": t, "path": f"f_{i}.py"} for i, t in enumerate(texts)], matrix)
    
    results = store.search(q_vec, top_k=2)
    assert len(results) == 2
    assert results[0][1] >= 0.0

def test_repository_indexing_and_retrieval():
    # Index demo repository
    indexer = RepositoryIndexer(repo_id="demo_test", repo_path=str(Config.DEMO_REPO_DIR))
    res = indexer.index()
    assert res["status"] == "success"
    assert res["total_files"] > 0
    assert res["total_chunks"] > 0

    retriever = RepositoryRetriever(repo_id="demo_test")
    chunks = retriever.retrieve("users database 500 error", top_k=3)
    assert len(chunks) > 0
    assert any("users" in c["path"] or "config" in c["path"] or "database" in c["path"] for c in chunks)
