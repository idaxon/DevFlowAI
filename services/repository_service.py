import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from database.db import db
from database.models import Repository
from rag.indexer import RepositoryIndexer
from config import Config

logger = logging.getLogger("devflow.services.repo")

class RepositoryService:
    """Manages repository registration, dynamic statistics analysis, and RAG status."""

    @staticmethod
    def register_or_get_demo_repo() -> Repository:
        """Ensure default demo repository is registered in DB with real stats."""
        repo = Repository.query.filter_by(name="flask-demo-api").first()
        stats = RepositoryService.inspect_local_repository(str(Config.DEMO_REPO_DIR))
        if not repo:
            repo = Repository(
                name="flask-demo-api",
                url="https://github.com/devflow-demo/flask-demo-api",
                local_path=str(Config.DEMO_REPO_DIR),
                branch="main",
                language=stats.get("language", "Python"),
                file_count=stats.get("file_count", 8),
                source_count=stats.get("source_count", 4),
                test_count=stats.get("test_count", 1),
                has_docker=stats.get("has_docker", True),
                has_ci=stats.get("has_ci", False),
                rag_status="indexed",
                status="active",
                last_commit="fix: initial user endpoint configuration"
            )
            db.session.add(repo)
            db.session.commit()
        else:
            # Refresh stats
            repo.file_count = stats.get("file_count", repo.file_count)
            repo.source_count = stats.get("source_count", repo.source_count)
            repo.test_count = stats.get("test_count", repo.test_count)
            repo.has_docker = stats.get("has_docker", repo.has_docker)
            repo.has_ci = stats.get("has_ci", repo.has_ci)
            repo.language = stats.get("language", repo.language)
            db.session.commit()
        return repo

    @staticmethod
    def inspect_local_repository(repo_path: str) -> Dict[str, Any]:
        """Deeply inspect folder to compute real language, file counts, tests, Docker, and CI files."""
        path = Path(repo_path)
        if not path.exists():
            return {
                "language": "Python",
                "file_count": 0,
                "source_count": 0,
                "test_count": 0,
                "has_docker": False,
                "has_ci": False,
                "branch": "main",
            }

        total_files = 0
        source_count = 0
        test_count = 0
        
        # Real Docker detection
        has_docker = (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists() or (path / "compose.yaml").exists()
        
        # Real CI detection
        has_ci = (path / ".github" / "workflows").exists() or (path / ".gitlab-ci.yml").exists() or (path / ".circleci").exists()

        languages = {}
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__", "dist", "build", ".pytest_cache")]
            for f in files:
                if f.startswith("."):
                    continue
                total_files += 1
                ext = os.path.splitext(f)[1].lower()
                f_lower = f.lower()

                # Test files identification
                if "test" in f_lower or "spec" in f_lower:
                    test_count += 1

                # Language detection
                if ext in (".py", ".pyw"):
                    languages["Python"] = languages.get("Python", 0) + 1
                    source_count += 1
                elif ext in (".js", ".jsx", ".mjs"):
                    languages["JavaScript"] = languages.get("JavaScript", 0) + 1
                    source_count += 1
                elif ext in (".ts", ".tsx"):
                    languages["TypeScript"] = languages.get("TypeScript", 0) + 1
                    source_count += 1
                elif ext in (".go",):
                    languages["Go"] = languages.get("Go", 0) + 1
                    source_count += 1
                elif ext in (".java",):
                    languages["Java"] = languages.get("Java", 0) + 1
                    source_count += 1
                elif ext in (".rs",):
                    languages["Rust"] = languages.get("Rust", 0) + 1
                    source_count += 1
                elif ext in (".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"):
                    languages["C/C++"] = languages.get("C/C++", 0) + 1
                    source_count += 1
                elif ext in (".php",):
                    languages["PHP"] = languages.get("PHP", 0) + 1
                    source_count += 1
                elif ext in (".rb",):
                    languages["Ruby"] = languages.get("Ruby", 0) + 1
                    source_count += 1
                elif ext in (".html", ".htm", ".css", ".scss"):
                    languages["HTML/CSS"] = languages.get("HTML/CSS", 0) + 1
                    source_count += 1

        primary_lang = max(languages, key=languages.get) if languages else "General"

        # Detect actual git branch if .git is present
        branch = "main"
        git_head = path / ".git" / "HEAD"
        if git_head.exists():
            try:
                head_content = git_head.read_text().strip()
                if head_content.startswith("ref: refs/heads/"):
                    branch = head_content.replace("ref: refs/heads/", "")
            except Exception:
                pass

        return {
            "language": primary_lang,
            "file_count": total_files,
            "source_count": source_count,
            "test_count": test_count,
            "has_docker": has_docker,
            "has_ci": has_ci,
            "branch": branch,
        }

    @staticmethod
    def index_repository(repo_id: int) -> Dict[str, Any]:
        """Index repository for vector RAG and update accurate counts."""
        repo = db.session.get(Repository, repo_id)
        if not repo:
            return {"status": "error", "message": "Repository not found"}

        repo.status = "indexing"
        db.session.commit()

        # Update stats
        stats = RepositoryService.inspect_local_repository(repo.local_path)
        repo.language = stats["language"]
        repo.file_count = stats["file_count"]
        repo.source_count = stats["source_count"]
        repo.test_count = stats["test_count"]
        repo.has_docker = stats["has_docker"]
        repo.has_ci = stats["has_ci"]
        repo.branch = stats["branch"]

        indexer = RepositoryIndexer(repo_id=str(repo.id), repo_path=repo.local_path)
        res = indexer.index()

        repo.status = "active"
        repo.rag_status = "indexed" if res.get("status") == "success" else "failed"
        db.session.commit()

        return res
