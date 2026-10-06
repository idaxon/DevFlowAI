import os
import subprocess
import zipfile
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, jsonify, request
from database.db import db
from database.models import Repository
from services.repository_service import RepositoryService
from config import Config

repositories_bp = Blueprint("repositories", __name__)

@repositories_bp.route("/repositories")
def list_repositories_view():
    repos = Repository.query.all()
    return render_template("repositories.html", repositories=repos, demo_mode=Config.DEMO_MODE)

@repositories_bp.route("/repositories/<int:repo_id>")
def repository_detail_view(repo_id):
    repo = db.session.get(Repository, repo_id)
    if not repo:
        return render_template("repositories.html", error="Repository not found"), 404
    return render_template("repository_detail.html", repository=repo, demo_mode=Config.DEMO_MODE)

@repositories_bp.route("/api/repositories", methods=["GET"])
def get_repositories_api():
    repos = Repository.query.all()
    return jsonify([r.to_dict() for r in repos])

@repositories_bp.route("/api/repositories/<int:repo_id>", methods=["GET"])
def get_repository_detail_api(repo_id):
    repo = db.session.get(Repository, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    return jsonify(repo.to_dict())

@repositories_bp.route("/api/repositories/upload", methods=["POST"])
def upload_repository_zip():
    """Handle custom repository upload via ZIP archive."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in request"}), 400

    file = request.files["file"]
    repo_name = request.form.get("name") or (file.filename.rsplit(".", 1)[0] if file.filename else "custom-repo")
    repo_name = secure_filename(repo_name).replace(" ", "-") or "custom-repo"

    if not file.filename or not file.filename.endswith(".zip"):
        return jsonify({"error": "Only .zip archive files are supported"}), 400

    target_dir = Config.ORIGINAL_REPO_DIR / repo_name
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract zip file
        with zipfile.ZipFile(file.stream, "r") as z:
            z.extractall(target_dir)

        # If extracted content is wrapped in a single root folder, unnest it
        extracted_items = list(target_dir.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            subfolder = extracted_items[0]
            temp_extract = Config.STORAGE_DIR / f"temp_{repo_name}"
            shutil.move(str(subfolder), str(temp_extract))
            shutil.rmtree(target_dir, ignore_errors=True)
            shutil.move(str(temp_extract), str(target_dir))

        stats = RepositoryService.inspect_local_repository(str(target_dir))

        repo = Repository(
            name=repo_name,
            url=f"local://{repo_name}",
            local_path=str(target_dir),
            branch=stats.get("branch", "main"),
            language=stats.get("language", "Python"),
            file_count=stats.get("file_count", 0),
            source_count=stats.get("source_count", 0),
            test_count=stats.get("test_count", 0),
            has_docker=stats.get("has_docker", False),
            has_ci=stats.get("has_ci", False),
            rag_status="unindexed",
            status="active",
            last_commit="Uploaded by user"
        )
        db.session.add(repo)
        db.session.commit()

        # Automatically index newly uploaded repo
        RepositoryService.index_repository(repo.id)

        return jsonify({
            "status": "success",
            "message": f"Repository '{repo_name}' uploaded and indexed successfully.",
            "repository": repo.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to extract and process repository: {str(e)}"}), 500

@repositories_bp.route("/api/repositories/connect", methods=["POST"])
def connect_repository():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    local_path = data.get("local_path", "").strip()

    if not name and url:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")
    if not name:
        return jsonify({"error": "Repository name is required"}), 400

    safe_name = secure_filename(name).replace(" ", "-") or "connected-repo"
    target_path = None

    # Option 1: Git URL provided
    if url and (url.startswith("http://") or url.startswith("https://") or url.startswith("git@")):
        cloned_dir = Config.STORAGE_DIR / "cloned" / safe_name
        if cloned_dir.exists():
            shutil.rmtree(cloned_dir, ignore_errors=True)
        cloned_dir.parent.mkdir(parents=True, exist_ok=True)

        clone_url = url
        # If GitHub token is present and it's a github.com HTTPS url without auth, embed token
        if Config.GITHUB_TOKEN and "github.com" in url and "://" in url:
            proto, rest = url.split("://", 1)
            if "@" not in rest:
                clone_url = f"{proto}://{Config.GITHUB_TOKEN}@{rest}"

        try:
            cmd = ["git", "clone", "--depth", "1", clone_url, str(cloned_dir)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                return jsonify({
                    "error": f"Git clone failed: {res.stderr.strip() or res.stdout.strip() or 'Unknown error'}"
                }), 400
            target_path = str(cloned_dir)
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Git clone timed out after 60s"}), 408
        except Exception as e:
            return jsonify({"error": f"Failed to clone git repository: {str(e)}"}), 500

    # Option 2: Local directory path provided
    elif local_path:
        p = Path(local_path).resolve()
        if not p.exists() or not p.is_dir():
            return jsonify({"error": f"Local path does not exist or is not a directory: {local_path}"}), 400
        target_path = str(p)

    # Option 3: Default fallback
    else:
        return jsonify({"error": "Please provide either a valid Git URL or a local folder path."}), 400

    stats = RepositoryService.inspect_local_repository(target_path)

    repo = Repository(
        name=name,
        url=url or f"local://{name}",
        local_path=target_path,
        branch=stats.get("branch", data.get("branch", "main")),
        language=stats.get("language", "Python"),
        file_count=stats.get("file_count", 0),
        source_count=stats.get("source_count", 0),
        test_count=stats.get("test_count", 0),
        has_docker=stats.get("has_docker", False),
        has_ci=stats.get("has_ci", False),
        rag_status="unindexed",
        status="active",
        last_commit="Connected by user"
    )
    db.session.add(repo)
    db.session.commit()

    # Index automatically
    RepositoryService.index_repository(repo.id)

    return jsonify({"status": "success", "repository": repo.to_dict()}), 201

@repositories_bp.route("/api/repositories/<int:repo_id>", methods=["DELETE"])
def delete_repository_api(repo_id):
    """Delete repository and its associated workspace files from storage."""
    repo = db.session.get(Repository, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    repo_name = repo.name
    repo_path = repo.local_path

    # Clean up files on disk if inside managed storage (cloned or uploaded), but do NOT delete demo repo folder
    try:
        p = Path(repo_path).resolve()
        storage_root = Config.STORAGE_DIR.resolve()
        demo_root = Config.DEMO_REPO_DIR.resolve()
        if p != demo_root and (storage_root in p.parents or p.parent == storage_root):
            shutil.rmtree(p, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Failed to clean up repository folder {repo_path}: {e}")

    db.session.delete(repo)
    db.session.commit()

    return jsonify({"status": "success", "message": f"Repository '{repo_name}' deleted successfully."})

@repositories_bp.route("/api/repositories/<int:repo_id>/index", methods=["POST"])
def index_repository_api(repo_id):
    res = RepositoryService.index_repository(repo_id)
    return jsonify(res)

@repositories_bp.route("/api/repositories/<int:repo_id>/refresh", methods=["POST"])
def refresh_repository_stats_api(repo_id):
    """Re-scan repository directory and update all stats in DB (language, file count, tests, etc.)."""
    repo = db.session.get(Repository, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    stats = RepositoryService.inspect_local_repository(repo.local_path)
    repo.language = stats["language"]
    repo.file_count = stats["file_count"]
    repo.source_count = stats["source_count"]
    repo.test_count = stats["test_count"]
    repo.has_docker = stats["has_docker"]
    repo.has_ci = stats["has_ci"]
    repo.branch = stats["branch"]
    db.session.commit()
    return jsonify({"status": "success", "repository": repo.to_dict()})


