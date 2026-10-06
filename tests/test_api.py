import pytest
from app import create_app
from database.db import db
from database.models import Workflow, Repository

@pytest.fixture
def app_instance():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_dashboard_api(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "metrics" in data
    assert "recent_workflows" in data

def test_repositories_api(client):
    res = client.get("/api/repositories")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)

def test_workflow_lifecycle_api(client):
    # Trigger workflow
    res = client.post("/api/workflows/run", json={
        "request": "Fix /users 500 error and validate container."
    })
    assert res.status_code == 201
    wf = res.get_json()["workflow"]
    wf_id = wf["id"]
    assert wf["status"] in ("QUEUED", "RUNNING", "AWAITING_APPROVAL", "SUCCESS")

    # Fetch workflow details
    detail_res = client.get(f"/api/workflows/{wf_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert detail_data["id"] == wf_id
    assert isinstance(detail_data.get("agent_runs"), list)

    # Human Approval
    appr_res = client.post(f"/api/workflows/{wf_id}/approve")
    assert appr_res.status_code == 200

    # Export report
    rep_res = client.get(f"/api/workflows/{wf_id}/report")
    assert rep_res.status_code == 200

def test_troubleshoot_endpoint(client):
    res = client.post("/api/troubleshoot", json={
        "query": "My Flask database fails during startup."
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "SUCCESS"
    assert "diagnosis" in data

def test_analytics_endpoint(client):
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.get_json()
    assert "metrics" in data
    assert "comparison" in data

def test_upload_repository_zip(client, tmp_path):
    import io
    import zipfile
    
    # Create an in-memory test zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("app.py", "from flask import Flask\napp = Flask(__name__)\n")
        z.writestr("tests/test_basic.py", "def test_ok(): assert True\n")
        z.writestr("requirements.txt", "flask>=3.0.0\n")

    zip_buffer.seek(0)
    data = {
        "name": "custom-uploaded-test",
        "file": (zip_buffer, "test_repo.zip")
    }
    res = client.post("/api/repositories/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["status"] == "success"
    assert json_data["repository"]["name"] == "custom-uploaded-test"
    assert json_data["repository"]["rag_status"] == "indexed"
