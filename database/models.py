import json
from datetime import datetime
from database.db import db

class Repository(db.Model):
    __tablename__ = "repositories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256), nullable=True)
    local_path = db.Column(db.String(512), nullable=False)
    branch = db.Column(db.String(64), default="main")
    language = db.Column(db.String(64), default="Python")
    status = db.Column(db.String(64), default="active") # active, indexing, error
    rag_status = db.Column(db.String(64), default="unindexed") # unindexed, indexed, failed
    file_count = db.Column(db.Integer, default=0)
    source_count = db.Column(db.Integer, default=0)
    test_count = db.Column(db.Integer, default=0)
    has_docker = db.Column(db.Boolean, default=False)
    has_ci = db.Column(db.Boolean, default=False)
    last_commit = db.Column(db.String(128), default="Initial commit")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflows = db.relationship("Workflow", backref="repository", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "local_path": self.local_path,
            "branch": self.branch,
            "language": self.language,
            "status": self.status,
            "rag_status": self.rag_status,
            "file_count": self.file_count,
            "source_count": self.source_count,
            "test_count": self.test_count,
            "has_docker": self.has_docker,
            "has_ci": self.has_ci,
            "last_commit": self.last_commit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Workflow(db.Model):
    __tablename__ = "workflows"

    id = db.Column(db.String(32), primary_key=True) # e.g. "DF-1024"
    repository_id = db.Column(db.Integer, db.ForeignKey("repositories.id"), nullable=True)
    request = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default="QUEUED") # QUEUED, RUNNING, SUCCESS, FAILED, AWAITING_APPROVAL, APPROVED, REJECTED
    current_step = db.Column(db.String(64), default="Intent Analysis")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    execution_time = db.Column(db.Float, default=0.0) # seconds
    approval_status = db.Column(db.String(32), default="PENDING") # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    pr_url = db.Column(db.String(256), nullable=True)
    pr_branch = db.Column(db.String(128), nullable=True)
    diff_content = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    error_summary = db.Column(db.Text, nullable=True)
    report_json_path = db.Column(db.String(256), nullable=True)

    agent_runs = db.relationship("AgentRun", backref="workflow", lazy=True, cascade="all, delete-orphan", order_by="AgentRun.started_at")
    diagnosis = db.relationship("Diagnosis", backref="workflow", uselist=False, lazy=True, cascade="all, delete-orphan")
    test_results = db.relationship("TestResult", backref="workflow", lazy=True, cascade="all, delete-orphan")
    deployments = db.relationship("Deployment", backref="workflow", lazy=True, cascade="all, delete-orphan")
    logs = db.relationship("SystemLog", backref="workflow", lazy=True, cascade="all, delete-orphan", order_by="SystemLog.timestamp")

    def to_dict(self):
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "repository_name": self.repository.name if self.repository else "Demo Workspace",
            "request": self.request,
            "status": self.status,
            "current_step": self.current_step,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": round(self.execution_time, 2),
            "approval_status": self.approval_status,
            "pr_url": self.pr_url,
            "pr_branch": self.pr_branch,
            "diff_content": self.diff_content,
            "retry_count": self.retry_count,
            "error_summary": self.error_summary,
            "agent_runs": [run.to_dict() for run in self.agent_runs],
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "test_result": self.test_results[-1].to_dict() if self.test_results else None,
            "deployment": self.deployments[-1].to_dict() if self.deployments else None,
        }


class AgentRun(db.Model):
    __tablename__ = "agent_runs"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(32), db.ForeignKey("workflows.id"), nullable=False)
    agent_name = db.Column(db.String(64), nullable=False) # IntentAgent, TroubleshootingAgent, DebuggingAgent, TestingAgent, DeploymentAgent, MonitoringAgent
    step_key = db.Column(db.String(64), nullable=False) # intent, repo_analysis, rag, troubleshoot, debug, test, docker, approval, report
    status = db.Column(db.String(32), default="WAITING") # WAITING, RUNNING, SUCCESS, FAILED, SKIPPED
    input_data = db.Column(db.Text, nullable=True)
    output_data = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    execution_time = db.Column(db.Float, default=0.0)
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        output_parsed = None
        if self.output_data:
            try:
                output_parsed = json.loads(self.output_data)
            except Exception:
                output_parsed = self.output_data

        input_parsed = None
        if self.input_data:
            try:
                input_parsed = json.loads(self.input_data)
            except Exception:
                input_parsed = self.input_data

        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "step_key": self.step_key,
            "status": self.status,
            "input": input_parsed,
            "output": output_parsed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time": round(self.execution_time, 2),
            "error_message": self.error_message,
        }


class Diagnosis(db.Model):
    __tablename__ = "diagnoses"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(32), db.ForeignKey("workflows.id"), nullable=False)
    root_cause = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float, default=0.0)
    affected_files_json = db.Column(db.Text, default="[]")
    evidence_json = db.Column(db.Text, default="[]")
    recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "root_cause": self.root_cause,
            "confidence": round(self.confidence * 100, 1) if self.confidence <= 1.0 else self.confidence,
            "confidence_raw": self.confidence,
            "affected_files": json.loads(self.affected_files_json or "[]"),
            "evidence": json.loads(self.evidence_json or "[]"),
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TestResult(db.Model):
    __tablename__ = "test_results"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(32), db.ForeignKey("workflows.id"), nullable=False)
    total = db.Column(db.Integer, default=0)
    passed = db.Column(db.Integer, default=0)
    failed = db.Column(db.Integer, default=0)
    skipped = db.Column(db.Integer, default=0)
    duration = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default="SUCCESS") # SUCCESS, FAILED, ERROR
    output_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration": round(self.duration, 2),
            "status": self.status,
            "output_details": self.output_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Deployment(db.Model):
    __tablename__ = "deployments"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(32), db.ForeignKey("workflows.id"), nullable=True)
    image = db.Column(db.String(128), default="devflow-test:latest")
    container_id = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(32), default="SUCCESS") # SUCCESS, FAILED, RUNNING, STOPPED, SIMULATED
    health_status = db.Column(db.String(32), default="HEALTHY") # HEALTHY, UNHEALTHY, UNKNOWN
    port = db.Column(db.Integer, default=5000)
    logs = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "image": self.image,
            "container_id": self.container_id,
            "status": self.status,
            "health_status": self.health_status,
            "port": self.port,
            "logs": self.logs,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SystemLog(db.Model):
    __tablename__ = "system_logs"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(32), db.ForeignKey("workflows.id"), nullable=True)
    level = db.Column(db.String(16), default="INFO") # INFO, SUCCESS, WARN, ERROR
    source = db.Column(db.String(64), nullable=False) # IntentAgent, TroubleshootingAgent, Git, Docker, System
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp.strftime("%H:%M:%S") if self.timestamp else "",
            "created_at": self.timestamp.isoformat() if self.timestamp else None,
        }
